// AI BFF Live Stage Controller - Client Application
let ws = null;
let recognition = null;
let isRecording = null;
let currentTimestamps = [];
let wordElements = [];
let animFrameId = null;

// State configuration
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
const karaokeContainer = document.getElementById('karaokeContainer');
const audioPlayer = document.getElementById('audioPlayer');
const micBtn = document.getElementById('micBtn');
const stopBtn = document.getElementById('stopBtn');
const resetBtn = document.getElementById('resetBtn');
const textForm = document.getElementById('textForm');
const textInput = document.getElementById('textInput');

// Initialize WebSockets
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    updateStatus('Connecting...', 'busy');

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        updateStatus('Connected', 'connected');
        sendConfig();
    };

    ws.onclose = () => {
        updateStatus('Disconnected (Reconnecting...)', 'error');
        setTimeout(initWebSocket, 2000);
    };

    ws.onerror = (err) => {
        console.error('WebSocket Error:', err);
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

function updateStatus(text, stateClass) {
    statusText.textContent = text;
    statusDot.className = 'status-indicator ' + (stateClass || '');
}

function sendConfig() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            action: 'set_config',
            ...currentConfig
        }));
    }
}

// Handle WebSocket Events
function handleServerEvent(data) {
    switch (data.event) {
        case 'connected':
        case 'config_updated':
            console.log('Config synchronized:', data);
            break;

        case 'status':
            if (data.state === 'generating_llm') {
                updateStatus('BFF Thinking...', 'busy');
                renderUserDialogue(data.user_text);
            } else if (data.state === 'generating_tts') {
                updateStatus('Synthesizing Voice...', 'busy');
                setEmotionBadge(data.emotion);
            }
            break;

        case 'turn_complete':
            updateStatus('Speaking', 'connected');
            playTurn(data);
            break;

        case 'audio_stopped':
            stopPlayback();
            updateStatus('Audio Stopped', 'connected');
            break;

        case 'context_reset':
            karaokeContainer.innerHTML = 'Conversation memory reset. Ready.';
            setEmotionBadge('ready');
            updateStatus('Ready', 'connected');
            break;

        case 'error':
            alert('Server Error: ' + data.message);
            updateStatus('Error', 'error');
            break;
    }
}

function renderUserDialogue(userText) {
    activeSpeaker.textContent = 'Shihab';
    activeEmotion.textContent = 'live';
    activeEmotion.className = 'emotion-badge';
    karaokeContainer.innerHTML = `<span style="color: #8b949e;">"${userText}"</span>`;
}

function setEmotionBadge(emotion) {
    if (!emotion) emotion = 'neutral';
    activeEmotion.textContent = emotion;
    activeEmotion.className = `emotion-badge ${emotion}`;
}

// Play Turn & Synchronize Karaoke Subtitles
function playTurn(turn) {
    activeSpeaker.textContent = `BFF (${turn.archetype})`;
    setEmotionBadge(turn.emotion);

    currentTimestamps = turn.timestamps || [];
    karaokeContainer.innerHTML = '';
    wordElements = [];

    // Render word spans
    currentTimestamps.forEach((t, idx) => {
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

    // Play Audio
    audioPlayer.src = turn.audio_url;
    audioPlayer.play().catch(e => {
        console.warn('Auto-play blocked or failed:', e);
    });

    // Start timestamp synchronization loop
    cancelAnimationFrame(animFrameId);
    syncKaraoke();
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
        animFrameId = requestAnimationFrame(syncKaraoke);
    } else {
        wordElements.forEach(el => el.classList.remove('active'));
    }
}

audioPlayer.addEventListener('ended', () => {
    cancelAnimationFrame(animFrameId);
    wordElements.forEach(el => el.classList.remove('active'));
    updateStatus('Ready', 'connected');
});

function stopPlayback() {
    audioPlayer.pause();
    audioPlayer.currentTime = 0;
    cancelAnimationFrame(animFrameId);
    wordElements.forEach(el => el.classList.remove('active'));
}

// Speech Recognition (Web Speech API)
function setupSpeechRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
        console.warn('Web Speech API not supported on this browser.');
        return;
    }

    recognition = new SpeechRec();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
        isRecording = true;
        micBtn.classList.add('recording');
        updateStatus('Listening to you...', 'busy');
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        if (transcript.trim()) {
            sendUserSpeech(transcript.trim());
        }
    };

    recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        stopRecordingUI();
        updateStatus('Ready', 'connected');
    };

    recognition.onend = () => {
        stopRecordingUI();
    };
}

function startRecording() {
    if (!recognition) setupSpeechRecognition();
    if (!recognition) {
        alert('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.');
        return;
    }
    try {
        recognition.start();
    } catch (e) {
        console.warn('Error starting speech:', e);
    }
}

function stopRecording() {
    if (recognition && isRecording) {
        recognition.stop();
    }
    stopRecordingUI();
}

function stopRecordingUI() {
    isRecording = false;
    micBtn.classList.remove('recording');
}

function sendUserSpeech(text) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ text }));
    }
}

// Event Listeners for Chips & Controls
document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
    setupSpeechRecognition();

    // Archetype selection
    document.querySelectorAll('#archetypeChips .chip').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#archetypeChips .chip').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            currentConfig.archetype = btn.dataset.archetype;
            sendConfig();
        });
    });

    // Attitude selection
    document.querySelectorAll('#attitudeChips .chip').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#attitudeChips .chip').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            currentConfig.attitude = btn.dataset.attitude;
            sendConfig();
        });
    });

    // Gender selection
    document.querySelectorAll('#genderChips .chip').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#genderChips .chip').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            currentConfig.gender = btn.dataset.gender;
            sendConfig();
        });
    });

    // Mic interaction (both tap and hold)
    micBtn.addEventListener('click', () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    });

    // Stop audio
    stopBtn.addEventListener('click', () => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'stop_audio' }));
        }
        stopPlayback();
    });

    // Reset memory
    resetBtn.addEventListener('click', () => {
        if (confirm('Clear AI BFF conversation memory?')) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: 'reset_context' }));
            }
        }
    });

    // Text form submission
    textForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const val = textInput.value.trim();
        if (val) {
            sendUserSpeech(val);
            textInput.value = '';
        }
    });
});
