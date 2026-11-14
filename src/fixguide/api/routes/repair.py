"""Repair API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from fixguide.graph.builder import graph
from fixguide.models.api import (
    ProductIdentifyRequest,
    ProductIdentifyResponse,
    StartRepairRequest,
    StartRepairResponse,
    StepQuestionRequest,
    StepQuestionResponse,
    StepVerifyRequest,
    StepVerifyResponse,
)
from fixguide.services.product_identifier import get_product_identifier
from fixguide.services.step_assistant import get_step_assistant

router = APIRouter()


@router.post("/identify", response_model=ProductIdentifyResponse)
async def identify_product(request: ProductIdentifyRequest) -> ProductIdentifyResponse:
    """Identify product brand, model, and category from a photo."""
    identifier = get_product_identifier()
    result = await identifier.identify_product(request.image_base64)
    return ProductIdentifyResponse(
        category=result["category"],
        device_name=result["device_name"],
        brand=result.get("brand", "Unknown"),
        model=result.get("model", "Unknown"),
        confidence=result.get("confidence", 0.8),
        visual_condition=result.get("visual_condition"),
    )


@router.post("/start", response_model=StartRepairResponse)
async def start_repair(request: StartRepairRequest) -> StartRepairResponse:
    """Start a new repair session."""
    session_id = str(uuid.uuid4())

    from fixguide.models.domain import RiskLevel
    from fixguide.models.state import GraphState

    device_spec = request.device_name or request.product_id

    initial_state = GraphState(
        session_id=session_id,
        category=request.category,
        product_id=device_spec,
        problem_description=request.problem_description,
        user_skill_level=request.user_skill_level,  # type: ignore
        available_tools=request.available_tools,
    )

    # Run graph until first step is displayed
    config = {"configurable": {"thread_id": session_id}}
    result = await graph.ainvoke(initial_state, config=config)

    risk_level = result.get("risk_level", RiskLevel.SAFE)

    return StartRepairResponse(
        session_id=session_id,
        risk_level=risk_level,
        first_step=result.get("generation_output"),
        message=(
            "Repair session started"
            if risk_level != RiskLevel.BLOCKED
            else "Repair not recommended for safety"
        ),
    )


@router.post("/verify", response_model=StepVerifyResponse)
async def verify_step(request: StepVerifyRequest) -> StepVerifyResponse:
    """Verify user's progress photo and advance."""
    config = {"configurable": {"thread_id": request.session_id}}

    # Update state on thread and resume from interrupted vision_check node
    await graph.aupdate_state(
        config,
        {
            "vision_input": request.image_base64,
            "user_notes": request.user_notes,
        },
    )
    result = await graph.ainvoke(None, config=config)

    vision_result = result.get("vision_result", {})
    generation_output = result.get("generation_output")

    return StepVerifyResponse(
        session_id=request.session_id,
        step_number=result.get("current_step", 0),
        matches_expected=vision_result.get("matches", False),
        feedback=vision_result.get("feedback", ""),
        next_step=generation_output,
        is_complete=result.get("is_complete", False),
        final_checklist=result.get("final_checklist", []),
    )


@router.post("/ask", response_model=StepQuestionResponse)
async def ask_step_question(request: StepQuestionRequest) -> StepQuestionResponse:
    """Answer a user question or provide advice about the current step."""
    assistant = get_step_assistant()
    answer = await assistant.answer_question(
        session_id=request.session_id,
        question=request.question,
        image_base64=request.image_base64,
    )
    return StepQuestionResponse(
        session_id=request.session_id,
        answer=answer,
    )
