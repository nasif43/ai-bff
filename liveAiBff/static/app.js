// AI BFF Live Stage Controller - Client Application
let ws = null;
let webSpeechRecognition = null;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let currentTimestamps = [];
let wordElements = [];
let animFrameId = null;
let audioUnlocked = false;

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
const userBubble = document.getElementById('userBubble');
const karaokeContainer = document.getElementById('karaokeContainer');
const audioPlayer = document.getElementById('audioPlayer');
const micBtn = document.getElementById('micBtn');
const micLabel = document.getElementById('micLabel');
const stopBtn = document.getElementById('stopBtn');
const resetBtn = document.getElementById('resetBtn');
const textInput = document.getElementById('textInput');
const sendBtn = document.getElementById('sendBtn');

// Unlock audio on first user touch/click anywhere
function unlockAudio() {
    if (audioUnlocked) return;
    audioPlayer.play().then(() => {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        audioUnlocked = true;
        console.log('[Audio] Unlocked successfully');
    }).catch(() => {
        // Expected if no audio loaded yet, marks intent
    });
}
document.addEventListener('click', unlockAudio, { once: false });
document.addEventListener('touchstart', unlockAudio, { once: false });

// Initialize WebSockets
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    updateStatus('Connecting...', 'busy');

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('[WS] Connected to server');
        updateStatus('Connected & Ready', 'connected');
        sendConfig();
    };

    ws.onclose = () => {
        console.warn('[WS] Closed. Reconnecting in 2s...');
        updateStatus('Reconnecting...', 'error');
        setTimeout(initWebSocket, 2000);
    };

    ws.onerror = (err) => {
        console.error('[WS] Error:', err);
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

// Handle WebSocket Events from Server
function handleServerEvent(data) {
    switch (data.event) {
        case 'connected':
        case 'config_updated':
            console.log('[WS] Synchronized config:', data);
            break;

        case 'status':
            if (data.state === 'generating_llm') {
                updateStatus('BFF Thinking...', 'busy');
            } else if (data.state === 'generating_tts') {
                updateStatus('Synthesizing Voice...', 'busy');
                setEmotionBadge(data.emotion);
            }
            break;

        case 'turn_complete':
            updateStatus('Speaking...', 'connected');
            playTurn(data);
            break;

        case 'audio_stopped':
            stopPlayback();
            updateStatus('Audio Stopped', 'connected');
            break;

        case 'context_reset':
            karaokeContainer.innerHTML = 'Conversation memory reset. Ready for next turn.';
            userBubble.style.display = 'none';
            setEmotionBadge('READY');
            updateStatus('Ready', 'connected');
            break;

        case 'error':
            alert('Server Error: ' + data.message);
            updateStatus('Ready', 'connected');
            break;
    }
}

function renderUserDialogue(text) {
    userBubble.style.display = 'block';
    userBubble.textContent = `You: "${text}"`;
    activeSpeaker.textContent = `AI BFF (${currentConfig.archetype})`;
    karaokeContainer.innerHTML = '<span style="color: #6b7280; font-style: italic;">Thinking of response...</span>';
}

function setEmotionBadge(emotion) {
    if (!emotion) emotion = 'neutral';
    activeEmotion.textContent = emotion.toUpperCase();
    activeEmotion.className = `emotion-badge ${emotion.toLowerCase()}`;
}

// Play Turn & Synchronize Karaoke Subtitles
function playTurn(turn) {
    activeSpeaker.textContent = `AI BFF (${turn.archetype})`;
    setEmotionBadge(turn.emotion);

    currentTimestamps = turn.timestamps || [];
    karaokeContainer.innerHTML = '';
    wordElements = [];

    // Render word spans
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

    // Play Audio
    audioPlayer.src = turn.audio_url;
    audioPlayer.currentTime = 0;
    
    const playPromise = audioPlayer.play();
    if (playPromise !== undefined) {
        playPromise.then(() => {
            cancelAnimationFrame(animFrameId);
            syncKaraoke();
        }).catch(e => {
            console.warn('Autoplay blocked by browser policy:', e);
            // Render manual play button so user can click to hear
            const playButton = document.createElement('button');
            playButton.type = 'button';
            playButton.className = 'pill-btn';
            playButton.style.marginTop = '12px';
            playButton.style.borderColor = 'var(--accent-cyan)';
            playButton.style.color = 'var(--accent-cyan)';
            playButton.innerHTML = '▶ Click to Listen';
            playButton.onclick = () => {
                audioPlayer.play();
                playButton.remove();
                syncKaraoke();
            };
            karaokeContainer.appendChild(document.createElement('br'));
            karaokeContainer.appendChild(playButton);
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

// Send user message turn to server
function sendUserSpeech(text) {
    const trimmed = text.trim();
    if (!trimmed) return;

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert('Connecting to server... Please wait a moment and try again.');
        return;
    }

    renderUserDialogue(trimmed);
    updateStatus('Thinking...', 'busy');
    ws.send(JSON.stringify({ text: trimmed }));
}

function handleSend() {
    const val = textInput.value;
    if (val && val.trim()) {
        sendUserSpeech(val);
        textInput.value = '';
    }
}

// ----------------------------------------------------
// DUAL-ENGINE MICROPHONE (WebSpeech + MediaRecorder + Whisper)
// ----------------------------------------------------

async function toggleRecording() {
    unlockAudio();
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

async function startRecording() {
    // Strategy A: Web Speech API
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRec) {
        try {
            webSpeechRecognition = new SpeechRec();
            webSpeechRecognition.continuous = false;
            webSpeechRecognition.interimResults = false;
            webSpeechRecognition.lang = 'en-US';

            webSpeechRecognition.onstart = () => {
                setRecordingState(true);
            };

            webSpeechRecognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                if (transcript && transcript.trim()) {
                    sendUserSpeech(transcript.trim());
                }
            };

            webSpeechRecognition.onerror = (event) => {
                console.warn('[WebSpeech] error:', event.error);
                // Fall back to MediaRecorder
                startMediaRecorder();
            };

            webSpeechRecognition.onend = () => {
                setRecordingState(false);
            };

            webSpeechRecognition.start();
            return;
        } catch (e) {
            console.warn('[WebSpeech] exception, trying MediaRecorder:', e);
        }
    }

    // Strategy B: MediaRecorder audio capture with Groq Whisper transcription
    startMediaRecorder();
}

async function startMediaRecorder() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showMicUnavailableAlert();
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioChunks = [];
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
            stream.getTracks().forEach(t => t.stop());
            if (audioChunks.length === 0) return;

            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            updateStatus('Transcribing speech (Whisper)...', 'busy');

            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');

            try {
                const res = await fetch('/api/stt', { method: 'POST', body: formData });
                const json = await res.json();
                if (json.text && json.text.trim()) {
                    sendUserSpeech(json.text.trim());
                } else {
                    updateStatus('No words detected. Try again.', 'connected');
                }
            } catch (err) {
                console.error('STT upload error:', err);
                updateStatus('STT Error', 'error');
            }
        };

        mediaRecorder.start();
        setRecordingState(true);
    } catch (err) {
        console.error('Microphone error:', err);
        setRecordingState(false);
        showMicUnavailableAlert();
    }
}

function stopRecording() {
    if (webSpeechRecognition) {
        try { webSpeechRecognition.stop(); } catch(e){}
    }
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        try { mediaRecorder.stop(); } catch(e){}
    }
    setRecordingState(false);
}

function setRecordingState(recording) {
    isRecording = recording;
    if (recording) {
        micBtn.classList.add('recording');
        micLabel.textContent = 'LISTENING... TAP TO STOP';
        updateStatus('Listening... (Tap to finish)', 'busy');
    } else {
        micBtn.classList.remove('recording');
        micLabel.textContent = 'TAP TO SPEAK';
    }
}

function showMicUnavailableAlert() {
    alert(
        'Microphone is blocked or unavailable on this browser origin.\n\n' +
        'Tip: Use the Quick Test chips or type in the message bar below!'
    );
}

// ----------------------------------------------------
// UI EVENT LISTENERS
// ----------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();

    // Archetype selection chips
    document.querySelectorAll('#archetypeChips .chip').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#archetypeChips .chip').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            currentConfig.archetype = btn.dataset.archetype;
            sendConfig();
        });
    });

    // Attitude selection chips
    document.querySelectorAll('#attitudeChips .chip').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#attitudeChips .chip').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            currentConfig.attitude = btn.dataset.attitude;
            sendConfig();
        });
    });

    // Gender selection chips
    document.querySelectorAll('#genderChips .chip').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#genderChips .chip').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            currentConfig.gender = btn.dataset.gender;
            sendConfig();
        });
    });

    // Quick Prompts chips
    document.querySelectorAll('.quick-chip').forEach(btn => {
        btn.addEventListener('click', () => {
            unlockAudio();
            const promptText = btn.dataset.prompt;
            if (promptText) sendUserSpeech(promptText);
        });
    });

    // Mic button
    micBtn.addEventListener('click', toggleRecording);

    // Stop button
    stopBtn.addEventListener('click', () => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'stop_audio' }));
        }
        stopPlayback();
    });

    // Reset button
    resetBtn.addEventListener('click', () => {
        if (confirm('Clear AI BFF conversation memory?')) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: 'reset_context' }));
            }
        }
    });

    // Send button click
    sendBtn.addEventListener('click', () => {
        unlockAudio();
        handleSend();
    });

    // Enter key on textInput
    textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            unlockAudio();
            handleSend();
        }
    });
});
