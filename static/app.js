// FixGuide AI Frontend
const API = '/api/v1/repair';
let sessionId = null;
let currentStep = 0;

// DOM Elements
const screens = { welcome: document.getElementById('welcome'), repair: document.getElementById('repair'), complete: document.getElementById('complete') };
const loading = document.getElementById('loading');
const startForm = document.getElementById('start-form');
const photoInput = document.getElementById('photo-input');
const photoBtn = document.getElementById('photo-btn');
const photoPreview = document.getElementById('photo-preview');
const verifyBtn = document.getElementById('verify-btn');
const backBtn = document.getElementById('back-btn');
const restartBtn = document.getElementById('restart-btn');
const stepInstruction = document.getElementById('step-instruction');
const stepNumber = document.getElementById('current-step-num');
const stepCounter = document.getElementById('step-counter');
const progressFill = document.getElementById('progress-fill');
const toolsList = document.getElementById('tools-list');
const safetyWarnings = document.getElementById('safety-warnings');
const verificationResult = document.getElementById('verification-result');
const checklist = document.getElementById('checklist');
const errorMessage = document.getElementById('error-message');
const deviceBadge = document.getElementById('device-badge');
const userNotesInput = document.getElementById('user-notes');
const identifyBtn = document.getElementById('identify-btn');
const identifyInput = document.getElementById('identify-input');
const identifyStatus = document.getElementById('identify-status');
const identifyThumb = document.getElementById('identify-thumb');
const identifyTitle = document.getElementById('identify-title');
const identifySub = document.getElementById('identify-sub');
const stepRefContainer = document.getElementById('step-ref-container');
const stepRefImg = document.getElementById('step-ref-img');
const qaForm = document.getElementById('qa-form');
const qaInput = document.getElementById('qa-input');
const qaMessages = document.getElementById('qa-messages');
const qaSubmitBtn = document.getElementById('qa-submit-btn');

// Show/hide screens
function showScreen(name) {
    Object.values(screens).forEach(s => s.classList.remove('active'));
    screens[name].classList.add('active');
}

function showLoading() { loading.classList.remove('hidden'); }
function hideLoading() { loading.classList.add('hidden'); }

function showError(msg) {
    errorMessage.textContent = msg;
    errorMessage.classList.remove('hidden');
}

// Auto-detect device from photo
if (identifyBtn && identifyInput) {
    identifyBtn.addEventListener('click', () => identifyInput.click());

    identifyInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (ev) => {
            const dataUrl = ev.target.result;
            const base64 = dataUrl.split(',')[1];

            identifyThumb.src = dataUrl;
            identifyStatus.classList.remove('hidden');
            identifyTitle.textContent = '🔍 Analyzing device with AI...';
            identifySub.textContent = 'Identifying brand, model, and physical condition';

            try {
                const res = await fetch(`${API}/identify`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image_base64: base64 })
                });

                if (!res.ok) {
                    throw new Error('Device detection failed');
                }

                const data = await res.json();
                document.getElementById('category').value = data.category;
                document.getElementById('device').value = data.device_name;

                identifyTitle.textContent = `✓ Detected: ${data.device_name}`;
                identifySub.textContent = `Category: ${data.category.replace('_', ' ').toUpperCase()}` +
                    (data.visual_condition ? ` • Condition: ${data.visual_condition}` : '');

                const problemEl = document.getElementById('problem');
                if (!problemEl.value.trim() && data.visual_condition) {
                    problemEl.value = data.visual_condition;
                }
            } catch (err) {
                identifyTitle.textContent = '⚠ Could not auto-detect product';
                identifySub.textContent = 'Please choose the category and enter the device name manually.';
            }
        };
        reader.readAsDataURL(file);
    });
}

// Start repair
startForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    showLoading();
    const tools = document.getElementById('tools').value
        ? document.getElementById('tools').value.split(',').map(t => t.trim())
        : [];

    const device = document.getElementById('device').value.trim();

    try {
        const res = await fetch(`${API}/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category: document.getElementById('category').value,
                device_name: device || null,
                problem_description: document.getElementById('problem').value,
                user_skill_level: document.getElementById('skill').value,
                available_tools: tools
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Failed to start repair');
        }

        const data = await res.json();
        sessionId = data.session_id;

        if (data.risk_level === 'blocked' || data.risk_level === 'high_risk') {
            showError(`Repair not recommended: ${data.risk_level}. Please seek professional assistance.`);
            return;
        }

        currentStep = 0;
        if (deviceBadge) {
            if (device) {
                deviceBadge.textContent = device;
                deviceBadge.classList.remove('hidden');
            } else {
                deviceBadge.classList.add('hidden');
            }
        }
        if (data.first_step) {
            displayStep(data.first_step, 1);
        }
        showScreen('repair');
    } catch (err) {
        showError(err.message);
    } finally {
        hideLoading();
    }
});

// Display a repair step
function displayStep(step, stepNum) {
    currentStep = stepNum;
    stepNumber.textContent = stepNum;
    stepCounter.textContent = `Step ${stepNum}`;
    stepInstruction.textContent = step.instruction || 'Follow the instructions above.';

    // Tools
    toolsList.innerHTML = '';
    (step.tools_required || []).forEach(t => {
        const span = document.createElement('span');
        span.textContent = t;
        toolsList.appendChild(span);
    });

    // Safety warnings
    safetyWarnings.innerHTML = '';
    (step.safety_flags || []).forEach(s => {
        const span = document.createElement('span');
        span.textContent = '⚠ ' + s;
        safetyWarnings.appendChild(span);
    });

    // Progress bar (estimate based on step number)
    progressFill.style.width = `${Math.min(stepNum * 10, 100)}%`;

    // iFixit reference images
    if (stepRefContainer && stepRefImg) {
        if (step.reference_images && step.reference_images.length > 0) {
            stepRefImg.src = step.reference_images[0];
            stepRefContainer.classList.remove('hidden');
        } else {
            stepRefContainer.classList.add('hidden');
        }
    }

    // Reset step Q&A for new step
    if (qaMessages) {
        qaMessages.innerHTML = '';
        qaMessages.classList.add('hidden');
    }
    if (qaInput) {
        qaInput.value = '';
    }
}

// Photo capture
photoBtn.addEventListener('click', () => photoInput.click());

photoInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        photoPreview.src = e.target.result;
        photoPreview.classList.remove('hidden');
        verifyBtn.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
});

// Verify step
verifyBtn.addEventListener('click', async () => {
    if (!photoInput.files[0]) return;

    showLoading();
    const base64 = photoPreview.src.split(',')[1];
    const userNotes = userNotesInput ? userNotesInput.value.trim() : '';

    try {
        const res = await fetch(`${API}/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                image_base64: base64,
                user_notes: userNotes || null
            })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Verification failed');
        }

        const data = await res.json();
        verificationResult.classList.remove('hidden');

        if (data.matches_expected) {
            verificationResult.className = 'verification-result success';
            verificationResult.textContent = '✓ Step verified! Great job.';

            if (data.is_complete) {
                displayChecklist(data.final_checklist);
                showScreen('complete');
            } else if (data.next_step) {
                displayStep(data.next_step, currentStep + 1);
                photoInput.value = '';
                if (userNotesInput) userNotesInput.value = '';
                photoPreview.classList.add('hidden');
                verifyBtn.classList.add('hidden');
            }
        } else {
            verificationResult.className = 'verification-result error';
            verificationResult.textContent = '✗ ' + (data.feedback || 'Does not match expected state. Try again.');
        }
    } catch (err) {
        showError(err.message);
    } finally {
        hideLoading();
    }
});

// Display reassembly checklist
function displayChecklist(items) {
    checklist.innerHTML = '';
    items.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        checklist.appendChild(li);
    });
}

// Back to welcome
backBtn.addEventListener('click', () => {
    sessionId = null;
    currentStep = 0;
    startForm.reset();
    verificationResult.classList.add('hidden');
    showScreen('welcome');
});

// Restart
restartBtn.addEventListener('click', () => {
    sessionId = null;
    currentStep = 0;
    startForm.reset();
    verificationResult.classList.add('hidden');
    showScreen('welcome');
});

// Step Assistant Q&A
if (qaForm) {
    qaForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = qaInput.value.trim();
        if (!question || !sessionId) return;

        const userMsg = document.createElement('div');
        userMsg.className = 'qa-msg qa-msg-user';
        userMsg.textContent = question;
        qaMessages.appendChild(userMsg);
        qaMessages.classList.remove('hidden');

        const botMsg = document.createElement('div');
        botMsg.className = 'qa-msg qa-msg-bot';
        botMsg.textContent = 'Thinking...';
        qaMessages.appendChild(botMsg);
        qaMessages.scrollTop = qaMessages.scrollHeight;

        qaInput.value = '';
        qaSubmitBtn.disabled = true;

        try {
            const res = await fetch(`${API}/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    question: question
                })
            });

            if (!res.ok) {
                throw new Error('Failed to get answer');
            }

            const data = await res.json();
            botMsg.textContent = data.answer;
        } catch (err) {
            botMsg.textContent = 'Sorry, could not answer right now. Please try again.';
        } finally {
            qaSubmitBtn.disabled = false;
            qaMessages.scrollTop = qaMessages.scrollHeight;
        }
    });
}