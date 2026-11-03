// AI BFF - Voice Interaction Engine
let ws = null;
let recognition = null;
let mediaRecorder = null;
let audioStream = null;
let recordedChunks = [];
let isRecording = false;
let isAutoCallMode = false;
let isAiSpeaking = false;
let audioUnlocked = false;
let karaokeAnimFrame = null;
let currentTimestamps = [];
let wordElements = [];

// Configuration State
let currentConfig = {
    archetype: 'DarkSoul',
    attitude: 'Delulu',
    gender: 'M',
};

// DOM Elements
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const activeSpeaker = document.getElementById('activeSpeaker');
const activeEmotion = document.getElementById('activeEmotion');
const stateCircle = document.getElementById('stateCircle');
const circleIcon = document.getElementById('circleIcon');
const circleLabel = document.getElementById('circleLabel');
const userBubble = document.getElementById('userBubble');
const karaokeContainer = document.getElementById('karaokeContainer');
const audioPlayer = document.getElementById('audioPlayer');
const micBtn = document.getElementById('micBtn');
const micButtonText = document.getElementById('micButtonText');
const callModeBtn = document.getElementById('callModeBtn');
const callModeLabel = document.getElementById('callModeLabel');
const stopBtn = document.getElementById('stopBtn');
const textToggleBtn = document.getElementById('textToggleBtn');
const textBar = document.getElementById('textBar');
const textInput = document.getElementById('textInput');
const sendBtn = document.getElementById('sendBtn');
const resetBtn = document.getElementById('resetBtn');

// ----------------------------------------------------
// 1. AUDIO UNLOCKING (Overcomes Browser Autoplay Restrictions)
// ----------------------------------------------------
function unlockAudio() {
    if (audioUnlocked) return;
    audioPlayer.play().then(() => {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        audioUnlocked = true;
        console.log('[Audio] Browser audio context unlocked');
    }).catch(() => {});
}
document.addEventListener('click', unlockAudio, { once: false });
document.addEventListener('touchstart', unlockAudio, { once: false });

// ----------------------------------------------------
// 2. WEBSOCKET SYNCHRONIZATION
// ----------------------------------------------------
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    updateStatus('Connecting...', 'busy');

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('[WS] Connected to live server');
        updateStatus('Connected & Ready', 'connected');
        sendConfig();
    };

    ws.onclose = () => {
        console.warn('[WS] Closed. Reconnecting in 2s...');
        updateStatus('Reconnecting...', 'error');
        setTimeout(initWebSocket, 2000);
    };

    ws.onerror = (err) => {
        console.error('[WS] Connection error:', err);
        updateStatus('Connection Error', 'error');
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleServerEvent(data);
        } catch (e) {
            console.error('Failed to parse WS payload:', e);
        }
    };
}

function sendConfig() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            action: 'set_config',
            ...currentConfig
        }));
    }
}

function updateStatus(text, stateClass) {
    statusText.textContent = text;
    statusDot.className = 'status-indicator ' + (stateClass || '');
}

function handleServerEvent(data) {
    switch (data.event) {
        case 'connected':
        case 'config_updated':
            console.log('[WS] Config synchronized:', data);
            break;

        case 'status':
            if (data.state === 'generating_llm') {
                setState('thinking', '⚡', 'THINKING...');
                updateStatus('BFF Thinking...', 'busy');
            } else if (data.state === 'generating_tts') {
                updateStatus('Synthesizing Voice...', 'busy');
                setEmotionBadge(data.emotion);
            }
            break;

        case 'turn_complete':
            playTurn(data);
            break;

        case 'audio_stopped':
            stopPlayback();
            break;

        case 'context_reset':
            karaokeContainer.innerHTML = 'Memory cleared. Ready for next turn.';
            userBubble.style.display = 'none';
            setEmotionBadge('READY');
            setState('idle', '🎙️', 'TAP TO TALK');
            updateStatus('Ready', 'connected');
            break;

        case 'error':
            alert('Server error: ' + data.message);
            setState('idle', '🎙️', 'TAP TO TALK');
            updateStatus('Ready', 'connected');
            break;
    }
}

// ----------------------------------------------------
// 3. PLAYBACK & SUBTITLE KARAOKE
// ----------------------------------------------------
function playTurn(turn) {
    isAiSpeaking = true;
    setState('speaking', '🔊', 'BFF SPEAKING');
    updateStatus('BFF Speaking...', 'connected');
    activeSpeaker.textContent = `AI BFF (${turn.archetype})`;
    setEmotionBadge(turn.emotion);

    currentTimestamps = turn.timestamps || [];
    karaokeContainer.innerHTML = '';
    wordElements = [];

    currentTimestamps.forEach((t) => {
        const span = document.createElement('span');
        span.className = 'karaoke-word';
        span.textContent = t.word;
        span.dataset.start = t.start;
        span.dataset.end = t.end;
        karaokeContainer.appendChild(span);
        wordElements.push(span);
    });

    if (currentTimestamps.length === 0) {
        karaokeContainer.textContent = turn.text;
    }

    audioPlayer.src = turn.audio_url;
    audioPlayer.currentTime = 0;

    const playPromise = audioPlayer.play();
    if (playPromise !== undefined) {
        playPromise.then(() => {
            cancelAnimationFrame(karaokeAnimFrame);
            syncKaraoke();
        }).catch(e => {
            console.warn('Autoplay caught:', e);
            const listenBtn = document.createElement('button');
            listenBtn.type = 'button';
            listenBtn.className = 'pill-btn';
            listenBtn.style.marginTop = '8px';
            listenBtn.style.borderColor = 'var(--accent-cyan)';
            listenBtn.style.color = 'var(--accent-cyan)';
            listenBtn.innerHTML = '▶ Click to Listen';
            listenBtn.onclick = () => {
                audioPlayer.play();
                listenBtn.remove();
                syncKaraoke();
            };
            karaokeContainer.appendChild(document.createElement('br'));
            karaokeContainer.appendChild(listenBtn);
        });
    }
}

function syncKaraoke() {
    if (!audioPlayer.paused && !audioPlayer.ended) {
        const curTime = audioPlayer.currentTime;
        for (let i = 0; i < currentTimestamps.length; i++) {
            const t = currentTimestamps[i];
            const el = wordElements[i];
            if (curTime >= t.start && curTime <= t.end + 0.05) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        }
        karaokeAnimFrame = requestAnimationFrame(syncKaraoke);
    } else {
        wordElements.forEach(el => el.classList.remove('active'));
    }
}

audioPlayer.addEventListener('ended', () => {
    isAiSpeaking = false;
    cancelAnimationFrame(karaokeAnimFrame);
    wordElements.forEach(el => el.classList.remove('active'));

    if (isAutoCallMode) {
        updateStatus('Listening... (Speak anytime)', 'connected');
        startVoiceCapture();
    } else {
        setState('idle', '🎙️', 'TAP TO TALK');
        updateStatus('Ready', 'connected');
    }
});

function stopPlayback() {
    isAiSpeaking = false;
    audioPlayer.pause();
    audioPlayer.currentTime = 0;
    cancelAnimationFrame(karaokeAnimFrame);
    wordElements.forEach(el => el.classList.remove('active'));
    setState('idle', '🎙️', 'TAP TO TALK');
}

function setEmotionBadge(emotion) {
    if (!emotion) emotion = 'neutral';
    activeEmotion.textContent = emotion.toUpperCase();
    activeEmotion.className = `emotion-badge ${emotion.toLowerCase()}`;
}

function setState(stateName, icon, label) {
    stateCircle.className = `state-circle ${stateName}`;
    circleIcon.textContent = icon;
    circleLabel.textContent = label;
}

function renderUserSpeech(text) {
    userBubble.style.display = 'block';
    userBubble.textContent = `You: "${text}"`;
    activeSpeaker.textContent = `AI BFF (${currentConfig.archetype})`;
    karaokeContainer.innerHTML = '<span style="color: #64748b; font-style: italic;">Thinking of response...</span>';
}

function sendTurnText(text) {
    const trimmed = text.trim();
    if (!trimmed) return;
    renderUserSpeech(trimmed);
    setState('thinking', '⚡', 'THINKING...');
    updateStatus('BFF Thinking...', 'busy');
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ text: trimmed }));
    }
}

// ----------------------------------------------------
// 4. SPEECH RECOGNITION & RECORDING
// ----------------------------------------------------
function startVoiceCapture() {
    unlockAudio();

    // If AI is currently speaking, barge-in stop
    if (isAiSpeaking) {
        stopPlayback();
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'stop_audio' }));
        }
    }

    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRec) {
        try {
            if (recognition) {
                try { recognition.abort(); } catch(e){}
            }

            recognition = new SpeechRec();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = 'en-US';

            recognition.onstart = () => {
                isRecording = true;
                setState('listening', '🎤', 'LISTENING...');
                updateStatus('Listening to you... Speak now', 'busy');
                micBtn.classList.add('recording');
                micButtonText.textContent = 'LISTENING... (TAP TO STOP)';
            };

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                if (transcript && transcript.trim()) {
                    sendTurnText(transcript.trim());
                }
            };

            recognition.onerror = (event) => {
                console.warn('[WebSpeech] error:', event.error);
                // Fall back to MediaRecorder on error
                if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
                    startMediaRecorderCapture();
                } else {
                    stopVoiceCaptureUI();
                }
            };

            recognition.onend = () => {
                stopVoiceCaptureUI();
            };

            recognition.start();
            return;
        } catch (e) {
            console.warn('[WebSpeech] exception, trying MediaRecorder:', e);
        }
    }

    startMediaRecorderCapture();
}

async function startMediaRecorderCapture() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert('Microphone access is not supported in this browser.');
        return;
    }

    try {
        if (audioStream) {
            audioStream.getTracks().forEach(t => t.stop());
        }

        audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        recordedChunks = [];

        let options = {};
        let ext = 'webm';
        if (typeof MediaRecorder.isTypeSupported === 'function') {
            if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
                options = { mimeType: 'audio/webm;codecs=opus' };
                ext = 'webm';
            } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
                options = { mimeType: 'audio/mp4' };
                ext = 'mp4';
            }
        }

        mediaRecorder = new MediaRecorder(audioStream, options);

        mediaRecorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) recordedChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
            if (audioStream) audioStream.getTracks().forEach(t => t.stop());
            if (recordedChunks.length === 0) return;

            const audioBlob = new Blob(recordedChunks, { type: options.mimeType || 'audio/webm' });
            recordedChunks = [];

            setState('thinking', '⚡', 'TRANSCRIBING...');
            updateStatus('Transcribing speech (Whisper)...', 'busy');

            const formData = new FormData();
            formData.append('audio', audioBlob, `recording.${ext}`);

            try {
                const res = await fetch('/api/stt', { method: 'POST', body: formData });
                const json = await res.json();
                if (json.text && json.text.trim()) {
                    sendTurnText(json.text.trim());
                } else {
                    setState('idle', '🎙️', 'TAP TO TALK');
                    updateStatus('No speech detected. Try again.', 'connected');
                }
            } catch (err) {
                console.error('STT upload error:', err);
                setState('idle', '🎙️', 'TAP TO TALK');
                updateStatus('STT Error', 'error');
            }
        };

        mediaRecorder.start();
        isRecording = true;
        setState('listening', '🎤', 'RECORDING...');
        updateStatus('Recording audio... Tap again to send', 'busy');
        micBtn.classList.add('recording');
        micButtonText.textContent = 'RECORDING... (TAP TO SEND)';
    } catch (err) {
        console.error('Microphone error:', err);
        stopVoiceCaptureUI();
        alert('Microphone access was denied. Please allow microphone permissions in your browser.');
    }
}

function stopVoiceCapture() {
    if (recognition) {
        try { recognition.stop(); } catch(e){}
    }
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        try { mediaRecorder.stop(); } catch(e){}
    }
    stopVoiceCaptureUI();
}

function stopVoiceCaptureUI() {
    isRecording = false;
    micBtn.classList.remove('recording');
    micButtonText.textContent = 'TAP TO SPEAK';
    if (!isAiSpeaking && stateCircle.className.includes('listening')) {
        setState('idle', '🎙️', 'TAP TO TALK');
    }
}

function toggleVoiceCapture() {
    if (isRecording) {
        stopVoiceCapture();
    } else {
        startVoiceCapture();
    }
}

// ----------------------------------------------------
// 5. EVENT LISTENERS
// ----------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();

    // Big central circle tap
    stateCircle.addEventListener('click', toggleVoiceCapture);

    // Mic button tap
    micBtn.addEventListener('click', toggleVoiceCapture);

    // Auto Call toggle
    callModeBtn.addEventListener('click', () => {
        unlockAudio();
        isAutoCallMode = !isAutoCallMode;
        if (isAutoCallMode) {
            callModeBtn.classList.add('active');
            callModeLabel.textContent = 'AUTO CALL ON';
            startVoiceCapture();
        } else {
            callModeBtn.classList.remove('active');
            callModeLabel.textContent = 'AUTO CALL';
            stopVoiceCapture();
            stopPlayback();
        }
    });

    // Interrupt / Stop button
    stopBtn.addEventListener('click', () => {
        stopPlayback();
        stopVoiceCapture();
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'stop_audio' }));
        }
    });

    // Reset conversation memory
    resetBtn.addEventListener('click', () => {
        if (confirm('Clear AI BFF conversation memory?')) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: 'reset_context' }));
            }
        }
    });

    // Collapsible text bar
    textToggleBtn.addEventListener('click', () => {
        textBar.style.display = (textBar.style.display === 'none') ? 'flex' : 'none';
        if (textBar.style.display === 'flex') textInput.focus();
    });

    sendBtn.addEventListener('click', () => {
        unlockAudio();
        const val = textInput.value.trim();
        if (val) {
            sendTurnText(val);
            textInput.value = '';
        }
    });

    textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            unlockAudio();
            const val = textInput.value.trim();
            if (val) {
                sendTurnText(val);
                textInput.value = '';
            }
        }
    });

    // Quick Trigger Chips
    document.querySelectorAll('.quick-chip').forEach(btn => {
        btn.addEventListener('click', () => {
            unlockAudio();
            const prompt = btn.dataset.prompt;
            if (prompt) sendTurnText(prompt);
        });
    });

    // Archetype Chips
    document.querySelectorAll('#archetypeChips .chip').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#archetypeChips .chip').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            currentConfig.archetype = btn.dataset.archetype;
            document.getElementById('activeArchetypeLabel').textContent = btn.textContent;
            sendConfig();
        });
    });

    // Attitude Chips
    document.querySelectorAll('#attitudeChips .chip').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#attitudeChips .chip').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            currentConfig.attitude = btn.dataset.attitude;
            document.getElementById('activeAttitudeLabel').textContent = btn.textContent;
            sendConfig();
        });
    });

    // Gender Chips
    document.querySelectorAll('#genderChips .chip').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#genderChips .chip').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            currentConfig.gender = btn.dataset.gender;
            sendConfig();
        });
    });
});
