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

// Repair History & Active Steps Elements
const historyList = document.getElementById('repair-history-list');
const completedStepsCard = document.getElementById('completed-steps-card');
const completedStepsList = document.getElementById('completed-steps-list');
const completedStepsCount = document.getElementById('completed-steps-count');

let completedSteps = [];
let currentRepairData = { category: '', device: '', problem: '' };

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
    const problem = document.getElementById('problem').value.trim();
    const category = document.getElementById('category').value;

    currentRepairData = {
        category: category,
        device: device || 'Hardware Device',
        problem: problem
    };
    completedSteps = [];
    renderCompletedSteps();

    try {
        const res = await fetch(`${API}/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category: category,
                device_name: device || null,
                problem_description: problem,
                user_skill_level: document.getElementById('skill').value,
                available_tools: tools
            })
        });

        if (!res.ok) {
            let errorMsg = 'Failed to start repair';
            try {
                const err = await res.json();
                errorMsg = err.detail || err.message || errorMsg;
            } catch {
                const text = await res.text();
                errorMsg = text || errorMsg;
            }
            throw new Error(errorMsg);
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
            let errorMsg = 'Verification failed';
            try {
                const err = await res.json();
                errorMsg = err.detail || err.message || errorMsg;
            } catch {
                const text = await res.text();
                errorMsg = text || errorMsg;
            }
            throw new Error(errorMsg);
        }

        const data = await res.json();
        verificationResult.classList.remove('hidden');

        if (data.matches_expected) {
            verificationResult.className = 'verification-result success';
            verificationResult.textContent = '✓ Step verified! Great job.';

            // Track completed step
            completedSteps.push({
                num: currentStep,
                instruction: stepInstruction.textContent
            });
            renderCompletedSteps();

            if (data.is_complete) {
                // Save completed repair session to history
                saveToHistory({
                    id: sessionId || 'rep-' + Date.now(),
                    category: currentRepairData.category,
                    device: currentRepairData.device,
                    problem: currentRepairData.problem,
                    stepsCount: completedSteps.length || currentStep,
                    date: 'Today, ' + new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    status: 'COMPLETED'
                });
                renderHistory();
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

// ==========================================================================
// Repair History & Step Log Handlers
// ==========================================================================

const DEFAULT_HISTORY = [
    {
        id: 'hist-1',
        category: 'game_controller',
        device: 'Sony PS5 DualSense',
        problem: 'Left analog stick drift and unresponsiveness',
        stepsCount: 4,
        date: 'Today, 2:45 PM',
        status: 'COMPLETED'
    },
    {
        id: 'hist-2',
        category: 'wired_headphones',
        device: 'Bose QuietComfort 45',
        problem: 'Audio cuts out when moving headphone wire or plug',
        stepsCount: 3,
        date: 'Yesterday, 6:15 PM',
        status: 'COMPLETED'
    },
    {
        id: 'hist-3',
        category: 'keyboard',
        device: 'Keychron Q1 Mechanical',
        problem: 'Keys chattering and repeating keystrokes',
        stepsCount: 3,
        date: '3 days ago',
        status: 'COMPLETED'
    }
];

function getCategoryIcon(cat) {
    const icons = {
        'game_controller': '🎮',
        'wired_headphones': '🎧',
        'keyboard': '⌨️',
        'remote_control': '📺',
        'lamp': '💡',
        'table_fan': '🌀'
    };
    return icons[cat] || '🔧';
}

function getHistory() {
    try {
        const stored = localStorage.getItem('fixguide_repair_history');
        if (stored) {
            const parsed = JSON.parse(stored);
            if (Array.isArray(parsed) && parsed.length > 0) return parsed;
        }
    } catch (e) {
        console.warn('Failed to parse history from localStorage', e);
    }
    return DEFAULT_HISTORY;
}

function saveToHistory(entry) {
    try {
        const history = getHistory().filter(h => h.id !== entry.id);
        history.unshift(entry);
        localStorage.setItem('fixguide_repair_history', JSON.stringify(history.slice(0, 8)));
    } catch (e) {
        console.warn('Failed to save to localStorage', e);
    }
}

function renderHistory() {
    if (!historyList) return;
    const history = getHistory();
    historyList.innerHTML = '';

    history.forEach(item => {
        const card = document.createElement('div');
        card.className = 'history-item';
        card.innerHTML = `
            <div class="history-icon-box">${getCategoryIcon(item.category)}</div>
            <div class="history-body">
                <div class="history-title-row">
                    <span class="history-device-name">${item.device || 'Hardware Device'}</span>
                    <span class="history-badge">${item.status || 'DONE'}</span>
                </div>
                <div class="history-problem">${item.problem}</div>
                <div class="history-meta">
                    <span>✓ ${item.stepsCount} Steps Verified</span> • <span>${item.date}</span>
                </div>
            </div>
        `;

        card.addEventListener('click', () => {
            // Populate Intake Form
            const catSelect = document.getElementById('category');
            if (catSelect && item.category) {
                catSelect.value = item.category;
                catSelect.dispatchEvent(new Event('change'));
                document.querySelectorAll('.cat-pill').forEach(pill => {
                    if (pill.getAttribute('data-cat') === item.category) {
                        pill.classList.add('active');
                    } else {
                        pill.classList.remove('active');
                    }
                });
            }

            const deviceInput = document.getElementById('device');
            if (deviceInput) deviceInput.value = item.device;

            const problemInput = document.getElementById('problem');
            if (problemInput) problemInput.value = item.problem;

            // Show full step-by-step history modal
            openHistoryModal(item);
        });

        historyList.appendChild(card);
    });
}

// Modal Elements
const historyModal = document.getElementById('history-modal');
const closeModalBtn = document.getElementById('close-modal-btn');
const modalDeviceTitle = document.getElementById('modal-device-title');
const modalDeviceProblem = document.getElementById('modal-device-problem');
const modalStepsContainer = document.getElementById('modal-steps-container');
const modalLoadBtn = document.getElementById('modal-load-btn');

let activeModalItem = null;

if (closeModalBtn && historyModal) {
    closeModalBtn.addEventListener('click', () => {
        historyModal.classList.add('hidden');
    });
    historyModal.addEventListener('click', (e) => {
        if (e.target === historyModal) {
            historyModal.classList.add('hidden');
        }
    });
}

function openHistoryModal(item) {
    if (!historyModal) return;
    activeModalItem = item;

    if (modalDeviceTitle) modalDeviceTitle.textContent = item.device || 'Hardware Device';
    if (modalDeviceProblem) modalDeviceProblem.textContent = item.problem;

    if (modalStepsContainer) {
        modalStepsContainer.innerHTML = '';

        // If PS5 controller, provide the exact 5 completed steps with photos
        const steps = item.steps || [
            {
                num: 1,
                title: 'Disconnect Battery Connector',
                desc: 'Carefully disconnect the battery connector from the mainboard using tweezers to avoid electrical shorts.',
                img: '/static/images/ps5_controller_battery_disconnect_macro_1794116769487.jpg'
            },
            {
                num: 2,
                title: 'Remove Battery Bracket',
                desc: 'Unscrew the battery bracket and lift out the tray to access internal motherboard ribbon cables.',
                img: '/static/images/ps5_controller_battery_tray_removal_1794116993213.jpg'
            },
            {
                num: 3,
                title: 'Release Joystick Ribbon Cable',
                desc: 'Lift the ZIF locking tab and disconnect the joystick module ribbon cable.',
                img: '/static/images/ps5_controller_ribbon_cable_disconnected_verification_1794118510088.jpg'
            },
            {
                num: 4,
                title: 'Clean Potentiometer Contacts',
                desc: 'Apply isopropyl alcohol to a cotton swab and gently clean the potentiometer wiper and contacts to clear stick drift.',
                img: '/static/images/ps5_controller_potentiometer_cleaning_macro_1794118809099.jpg'
            },
            {
                num: 5,
                title: 'Reassembly & Shell Verification',
                desc: 'Reinstall joystick module, secure screws, reconnect battery, and close the shell until all clips engage.',
                img: '/static/images/dualsense_black_rear.jpg'
            }
        ];

        steps.forEach(s => {
            const stepCard = document.createElement('div');
            stepCard.className = 'modal-step-card';
            stepCard.innerHTML = `
                <div class="modal-step-title">
                    <span style="background: rgba(46, 125, 50, 0.12); color: #2E7D32; padding: 2px 8px; border-radius: 6px; font-size: 11px;">STEP ${s.num}</span>
                    <span>${s.title}</span>
                </div>
                <div style="font-size: 12.5px; color: var(--text-body); line-height: 1.5;">${s.desc}</div>
                ${s.img ? `<img src="${s.img}" class="modal-step-img" alt="${s.title}" loading="lazy">` : ''}
            `;
            modalStepsContainer.appendChild(stepCard);
        });
    }

    historyModal.classList.remove('hidden');
}

if (modalLoadBtn) {
    modalLoadBtn.addEventListener('click', () => {
        if (!activeModalItem) return;
        historyModal.classList.add('hidden');

        // Populate Form
        const catSelect = document.getElementById('category');
        if (catSelect && activeModalItem.category) {
            catSelect.value = activeModalItem.category;
            catSelect.dispatchEvent(new Event('change'));
            document.querySelectorAll('.cat-pill').forEach(pill => {
                if (pill.getAttribute('data-cat') === activeModalItem.category) {
                    pill.classList.add('active');
                } else {
                    pill.classList.remove('active');
                }
            });
        }

        const deviceInput = document.getElementById('device');
        if (deviceInput) deviceInput.value = activeModalItem.device;

        const problemInput = document.getElementById('problem');
        if (problemInput) problemInput.value = activeModalItem.problem;

        // Auto-switch directly into the completed repair screen or cockpit
        sessionId = 'hist-resume-' + Date.now();
        if (deviceBadge) {
            deviceBadge.textContent = activeModalItem.device;
            deviceBadge.classList.remove('hidden');
        }

        displayChecklist([
            "Verify analog stick movement smoothly in 360 degrees",
            "Confirm all face buttons and triggers operate with tactile feedback",
            "Ensure battery holds charge and connects via USB/Bluetooth",
            "Perform stick calibration on gamepad-tester.com"
        ]);
        showScreen('complete');
    });
}

function renderCompletedSteps() {
    if (!completedStepsCard || !completedStepsList) return;
    if (completedSteps.length === 0) {
        completedStepsCard.classList.add('hidden');
        return;
    }

    completedStepsCard.classList.remove('hidden');
    if (completedStepsCount) {
        completedStepsCount.textContent = `${completedSteps.length} VERIFIED`;
    }

    completedStepsList.innerHTML = '';
    completedSteps.forEach(step => {
        const row = document.createElement('div');
        row.className = 'step-history-row';
        row.innerHTML = `
            <div class="step-history-check">✓</div>
            <div style="flex: 1;">
                <strong style="color: var(--burgundy-deep);">Step ${step.num}:</strong>
                <span style="color: var(--text-muted); margin-left: 4px;">${step.instruction}</span>
            </div>
        `;
        completedStepsList.appendChild(row);
    });
}

// Initial render
renderHistory();
