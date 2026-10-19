"""LangGraph node implementations."""

from __future__ import annotations

from typing import cast

from fixguide.core.generation import get_generator, get_verifier
from fixguide.core.retrieval import get_retriever
from fixguide.core.risk import get_risk_gate
from fixguide.core.verification import get_vision_verifier
from fixguide.models.domain import RepairStep
from fixguide.models.state import GraphState


async def risk_gate_node(state: GraphState) -> GraphState:
    """Classify product risk level — hard gate before any generation."""
    gate = get_risk_gate()
    state.risk_level = gate.classify(
        state.category.value,
        state.problem_description,
        state.user_skill_level,
    )

    if state.risk_level in ("high_risk", "blocked"):
        state.next_action = "error"
        state.error = f"Repair not recommended: {state.risk_level.value}"
    else:
        state.next_action = "retrieve"

    return state


async def retrieve_node(state: GraphState) -> GraphState:
    """Hybrid retrieval: BM25 + dense vector search."""
    retriever = get_retriever()
    query_parts = [state.category.value]
    if state.product_id:
        query_parts.append(state.product_id)
    query_parts.append(state.problem_description)
    query = " ".join(query_parts)
    results = retriever.search(query, state.category, top_k=10)

    state.retrieval_results = [r.model_dump() for r in results]
    state.next_action = "generate" if results else "error"

    if not results:
        state.error = "No relevant repair procedures found"

    return state


async def generate_node(state: GraphState) -> GraphState:
    """Generate next repair step with citations."""
    generator = get_generator()

    step_num = state.current_step + 1
    result = await generator.generate(
        category=state.category.value,
        product_id=state.product_id,
        problem=state.problem_description,
        skill_level=state.user_skill_level,
        tools=state.available_tools,
        current_step=step_num,
        chunks=state.retrieval_results,
    )

    if result.get("is_complete"):
        state.is_complete = True
        state.final_checklist = result.get("final_checklist", [])
        state.next_action = "reassembly"
    else:
        from fixguide.services.ifixit import get_ifixit_service

        ifixit = get_ifixit_service()
        search_target = (
            state.product_id
            or f"{state.category.value.replace('_', ' ')} {state.problem_description}"
        )
        ref_images = await ifixit.get_step_images(search_target, step_num)
        if not ref_images and state.product_id:
            ref_images = await ifixit.get_step_images(
                state.category.value.replace("_", " "), step_num
            )

        result["reference_images"] = ref_images
        state.generation_output = result
        state.next_action = "verify"

    return state


async def verify_node(state: GraphState) -> GraphState:
    """Grounding verifier: every claim must trace to a source chunk."""
    verifier = get_verifier()

    if not state.generation_output:
        state.verification_result = {"grounded": False, "feedback": "No step to verify"}
        state.next_action = "generate"
        return state

    result = await verifier.verify(state.generation_output, state.retrieval_results)
    state.verification_result = result

    if result.get("grounded") or state.retry_count >= 1:
        state.next_action = "vision_check"
    else:
        state.retry_count += 1
        state.next_action = "generate"  # retry with feedback

    return state


async def vision_check_node(state: GraphState) -> GraphState:
    """Vision verifier: compare user photo to expected step state."""
    verifier = get_vision_verifier()

    if not state.vision_input:
        state.vision_result = {"matches": False, "feedback": "No image provided"}
        state.next_action = "generate"
        return state

    step = state.generation_output or {}
    result = await verifier.verify(
        image_base64=state.vision_input,
        step_number=state.current_step + 1,
        expected_state=step.get("expected_visual_state", ""),
        components=step.get("components_involved", []),
        user_notes=state.user_notes,
    )

    state.vision_result = result
    state.vision_input = None  # consume input
    state.user_notes = None  # consume input

    if result.get("matches"):
        # Advance step
        state.current_step += 1
        state.completed_steps.append(state.current_step)
        if state.generation_output:
            state.steps.append(cast(RepairStep, state.generation_output))

        if state.is_complete:
            state.next_action = "reassembly"
        else:
            state.next_action = "retrieve"
    else:
        # Correction loop - regenerate with feedback
        state.next_action = "generate"

    return state


async def reassembly_node(state: GraphState) -> GraphState:
    """Generate reassembly checklist and final test procedure using LLM."""
    import json

    from fixguide.services.llm import get_llm_client
    from fixguide.utils.prompts import render_prompt

    client = get_llm_client()
    prompt = render_prompt(
        "reassembly",
        {
            "category": state.category.value,
            "steps": [
                {"step_number": s.step_number, "instruction": s.instruction} for s in state.steps
            ],
        },
    )

    try:
        response = await client.chat_completion(
            [
                {"role": "system", "content": prompt["system"]},
                {"role": "user", "content": prompt["user"]},
            ]
        )
        result = json.loads(response)
        state.final_checklist = result.get("checklist", [])
        state.final_checklist.extend(result.get("test_procedure", []))
        state.final_checklist.extend(result.get("safety_checks", []))
    except Exception:
        # Fallback to template
        state.final_checklist = [
            "Reassemble in reverse order of disassembly",
            "Verify all screws are tightened",
            "Reconnect all cables and ribbons",
            "Replace all covers and casings",
            "Test basic functionality",
        ]

    state.is_complete = True
    state.next_action = "complete"
    return state
