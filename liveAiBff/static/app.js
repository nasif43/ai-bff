// AI BFF - Real-Time Full-Duplex Voice Engine
let ws = null;
let audioContext = null;
let analyser = null;
let micStream = null;
let isCallActive = false;
let isUserSpeaking = false;
let isAiSpeaking = false;
let vadTimer = null;
let speechStartTime = 0;
let lastSpeechTime = 0;
let webSpeechRecognition = null;
let mediaRecorder = null;
let recordedChunks = [];
let animFrameId = null;
let karaokeAnimFrame = null;
let currentTimestamps = [];
let wordElements = [];
let audioUnlocked = false;

// Configuration state
let currentConfig = {
    archetype: 'DarkSoul',
    attitude: 'Delulu',
    gender: 'M',
};

// VAD parameters
const VAD_VOLUME_THRESHOLD = 16;     // RMS speech trigger sensitivity
const VAD_SILENCE_DURATION = 750;     // Milliseconds of silence after speech to commit turn
const VAD_MIN_SPEECH_DURATION = 350;  // Ignore mouth clicks / short noises

// DOM Elements
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const activeSpeaker = document.getElementById('activeSpeaker');
const activeEmotion = document.getElementById('activeEmotion');
const liveIndicator = document.getElementById('liveIndicator');
const turnTiming = document.getElementById('turnTiming');
const userBubble = document.getElementById('userBubble');
const karaokeContainer = document.getElementById('karaokeContainer');
const audioPlayer = document.getElementById('audioPlayer');
const callToggleBtn = document.getElementById('callToggleBtn');
const callBtnText = document.getElementById('callBtnText');
const stopBtn = document.getElementById('stopBtn');
const textToggleBtn = document.getElementById('textToggleBtn');
const textBar = document.getElementById('textBar');
const textInput = document.getElementById('textInput');
const sendBtn = document.getElementById('sendBtn');
const resetBtn = document.getElementById('resetBtn');
const canvas = document.getElementById('visualizerCanvas');
const canvasCtx = canvas.getContext('2d');

// ----------------------------------------------------
// 1. WEBSOCKET ORCHESTRATION
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
                updateStatus('BFF Thinking...', 'busy');
                liveIndicator.textContent = 'THINKING...';
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
            updateStatus('Ready', 'connected');
            break;

        case 'error':
            alert('Server error: ' + data.message);
            updateStatus('Ready', 'connected');
            break;
    }
}

// ----------------------------------------------------
// 2. REAL-TIME PLAYBACK & SUBTITLE KARAOKE
// ----------------------------------------------------
function playTurn(turn) {
    isAiSpeaking = true;
    updateStatus('BFF Speaking...', 'connected');
    liveIndicator.textContent = 'BFF SPEAKING';
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

    turnTiming.textContent = `${turn.duration || 0}s`;

    audioPlayer.src = turn.audio_url;
    audioPlayer.currentTime = 0;

    const playPromise = audioPlayer.play();
    if (playPromise !== undefined) {
        playPromise.then(() => {
            cancelAnimationFrame(karaokeAnimFrame);
            syncKaraoke();
        }).catch(e => {
            console.warn('Autoplay policy caught:', e);
            const listenBtn = document.createElement('button');
            listenBtn.type = 'button';
            listenBtn.className = 'pill-btn';
            listenBtn.style.marginTop = '8px';
            listenBtn.style.borderColor = 'var(--accent-cyan)';
            listenBtn.style.color = 'var(--accent-cyan)';
            listenBtn.innerHTML = '▶ Tap to Listen';
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
    if (isCallActive) {
        updateStatus('Listening... (Speak anytime)', 'connected');
        liveIndicator.textContent = 'LISTENING...';
    } else {
        updateStatus('Ready', 'connected');
        liveIndicator.textContent = 'READY';
    }
});

function stopPlayback() {
    isAiSpeaking = false;
    audioPlayer.pause();
    audioPlayer.currentTime = 0;
    cancelAnimationFrame(karaokeAnimFrame);
    wordElements.forEach(el => el.classList.remove('active'));
    liveIndicator.textContent = isCallActive ? 'LISTENING...' : 'READY';
}

function setEmotionBadge(emotion) {
    if (!emotion) emotion = 'neutral';
    activeEmotion.textContent = emotion.toUpperCase();
    activeEmotion.className = `emotion-badge ${emotion.toLowerCase()}`;
}

function renderUserSpeech(text) {
    userBubble.style.display = 'block';
    userBubble.textContent = `You: "${text}"`;
    activeSpeaker.textContent = `AI BFF (${currentConfig.archetype})`;
    karaokeContainer.innerHTML = '<span style="color: #64748b; font-style: italic;">Thinking...</span>';
}

function sendTurnText(text) {
    const trimmed = text.trim();
    if (!trimmed) return;
    renderUserSpeech(trimmed);
    updateStatus('BFF Thinking...', 'busy');
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ text: trimmed }));
    }
}

// ----------------------------------------------------
// 3. FULL-DUPLEX VOICE ACTIVITY DETECTION (VAD)
// ----------------------------------------------------
async function startLiveCall() {
    try {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }

        micStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
            }
        });

        const source = audioContext.createMediaStreamSource(micStream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);

        setupWebSpeechOrMediaRecorder(micStream);

        isCallActive = true;
        callToggleBtn.className = 'call-toggle-btn active';
        callBtnText.textContent = 'END LIVE CALL';
        updateStatus('Live Call Connected - Speak anytime', 'connected');
        liveIndicator.textContent = 'LISTENING...';

        startVisualizerLoop();
        startVadLoop();
    } catch (e) {
        console.error('Failed to start live call:', e);
        alert('Could not access microphone: ' + e.message);
    }
}

function stopLiveCall() {
    isCallActive = false;
    isUserSpeaking = false;
    clearTimeout(vadTimer);

    if (micStream) {
        micStream.getTracks().forEach(t => t.stop());
        micStream = null;
    }
    if (webSpeechRecognition) {
        try { webSpeechRecognition.stop(); } catch(e){}
    }
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        try { mediaRecorder.stop(); } catch(e){}
    }

    stopPlayback();

    callToggleBtn.className = 'call-toggle-btn idle';
    callBtnText.textContent = 'START LIVE CALL';
    updateStatus('Call Ended - Ready', 'connected');
    liveIndicator.textContent = 'READY';
}

function setupWebSpeechOrMediaRecorder(stream) {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRec) {
        try {
            webSpeechRecognition = new SpeechRec();
            webSpeechRecognition.continuous = true;
            webSpeechRecognition.interimResults = true;
            webSpeechRecognition.lang = 'en-US';

            webSpeechRecognition.onresult = (event) => {
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        const finalTranscript = event.results[i][0].transcript.trim();
                        if (finalTranscript) {
                            sendTurnText(finalTranscript);
                        }
                    }
                }
            };

            webSpeechRecognition.onerror = (e) => {
                console.warn('[WebSpeech] Fallback triggered:', e.error);
                setupMediaRecorderFallback(stream);
            };

            webSpeechRecognition.onend = () => {
                if (isCallActive) {
                    try { webSpeechRecognition.start(); } catch(e){}
                }
            };

            webSpeechRecognition.start();
            return;
        } catch(e) {
            console.warn('SpeechRecognition failed, using MediaRecorder:', e);
        }
    }

    setupMediaRecorderFallback(stream);
}

function setupMediaRecorderFallback(stream) {
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

    mediaRecorder = new MediaRecorder(stream, options);
    recordedChunks = [];

    mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) recordedChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
        if (recordedChunks.length === 0) return;
        const blob = new Blob(recordedChunks, { type: options.mimeType || 'audio/webm' });
        recordedChunks = [];

        const formData = new FormData();
        formData.append('audio', blob, `recording.${ext}`);

        try {
            const res = await fetch('/api/stt', { method: 'POST', body: formData });
            const json = await res.json();
            if (json.text && json.text.trim()) {
                sendTurnText(json.text.trim());
            }
        } catch (err) {
            console.error('STT error:', err);
        }
    };
}

// Real-time Voice Activity Detection (VAD) audio loop
function startVadLoop() {
    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    function checkAudio() {
        if (!isCallActive) return;

        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i];
        }
        const volume = sum / dataArray.length;
        const now = Date.now();

        if (volume > VAD_VOLUME_THRESHOLD) {
            // User is actively speaking!
            if (!isUserSpeaking) {
                isUserSpeaking = true;
                speechStartTime = now;
                liveIndicator.textContent = 'YOU ARE SPEAKING';

                // BARGE-IN: If AI was speaking, instantly interrupt it!
                if (isAiSpeaking) {
                    stopPlayback();
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ action: 'stop_audio' }));
                    }
                }

                // If using MediaRecorder fallback, start slice
                if (mediaRecorder && mediaRecorder.state === 'inactive') {
                    recordedChunks = [];
                    mediaRecorder.start();
                }
            }
            lastSpeechTime = now;
            clearTimeout(vadTimer);
        } else {
            // Silence
            if (isUserSpeaking && (now - lastSpeechTime > VAD_SILENCE_DURATION)) {
                if (now - speechStartTime > VAD_MIN_SPEECH_DURATION) {
                    // Turn committed by silence!
                    isUserSpeaking = false;
                    liveIndicator.textContent = 'PROCESSING...';

                    if (mediaRecorder && mediaRecorder.state === 'recording') {
                        mediaRecorder.stop();
                    }
                } else {
                    // Too short (mouth click / background pop)
                    isUserSpeaking = false;
                    if (mediaRecorder && mediaRecorder.state === 'recording') {
                        mediaRecorder.stop();
                        recordedChunks = [];
                    }
                }
            }
        }

        requestAnimationFrame(checkAudio);
    }

    requestAnimationFrame(checkAudio);
}

// ----------------------------------------------------
// 4. ANIMATED VOICE ORB VISUALIZER
// ----------------------------------------------------
function startVisualizerLoop() {
    const bufferLength = analyser ? analyser.frequencyBinCount : 32;
    const dataArray = new Uint8Array(bufferLength);

    function render() {
        if (!isCallActive) {
            renderIdleOrb();
            return;
        }

        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i];
        }
        const energy = sum / bufferLength;

        const w = canvas.width;
        const h = canvas.height;
        const centerX = w / 2;
        const centerY = h / 2;
        canvasCtx.clearRect(0, 0, w, h);

        // Dynamic radius reacting to voice
        const baseRadius = 55;
        const dynamicRadius = baseRadius + (energy * 0.9);

        // Color shifts based on speaking state
        let strokeColor = 'rgba(0, 240, 255, 0.8)';
        let glowColor = 'rgba(0, 240, 255, 0.4)';
        if (isUserSpeaking) {
            strokeColor = 'rgba(0, 230, 118, 0.9)';
            glowColor = 'rgba(0, 230, 118, 0.5)';
        } else if (isAiSpeaking) {
            strokeColor = 'rgba(255, 42, 133, 0.9)';
            glowColor = 'rgba(255, 42, 133, 0.5)';
        }

        // Draw glowing concentric rings
        canvasCtx.save();
        canvasCtx.shadowBlur = 24;
        canvasCtx.shadowColor = glowColor;

        canvasCtx.beginPath();
        canvasCtx.arc(centerX, centerY, dynamicRadius, 0, 2 * Math.PI);
        canvasCtx.fillStyle = 'rgba(15, 18, 26, 0.85)';
        canvasCtx.fill();
        canvasCtx.lineWidth = 3;
        canvasCtx.strokeStyle = strokeColor;
        canvasCtx.stroke();

        // Draw frequency ripple waves
        canvasCtx.beginPath();
        for (let i = 0; i < bufferLength; i += 4) {
            const angle = (i / bufferLength) * 2 * Math.PI;
            const waveR = dynamicRadius + (dataArray[i] * 0.25);
            const x = centerX + waveR * Math.cos(angle);
            const y = centerY + waveR * Math.sin(angle);
            if (i === 0) canvasCtx.moveTo(x, y);
            else canvasCtx.lineTo(x, y);
        }
        canvasCtx.closePath();
        canvasCtx.strokeStyle = glowColor;
        canvasCtx.lineWidth = 2;
        canvasCtx.stroke();

        canvasCtx.restore();

        animFrameId = requestAnimationFrame(render);
    }

    render();
}

function renderIdleOrb() {
    const w = canvas.width;
    const h = canvas.height;
    const centerX = w / 2;
    const centerY = h / 2;
    canvasCtx.clearRect(0, 0, w, h);

    canvasCtx.save();
    canvasCtx.shadowBlur = 18;
    canvasCtx.shadowColor = 'rgba(0, 240, 255, 0.3)';

    canvasCtx.beginPath();
    canvasCtx.arc(centerX, centerY, 58, 0, 2 * Math.PI);
    canvasCtx.fillStyle = 'rgba(15, 18, 26, 0.9)';
    canvasCtx.fill();
    canvasCtx.lineWidth = 2.5;
    canvasCtx.strokeStyle = 'rgba(0, 240, 255, 0.6)';
    canvasCtx.stroke();

    canvasCtx.restore();
}

// ----------------------------------------------------
// 5. EVENT LISTENERS
// ----------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    initWebSocket();
    renderIdleOrb();

    // Call toggle button (Start/End Call)
    callToggleBtn.addEventListener('click', () => {
        if (!isCallActive) {
            startLiveCall();
        } else {
            stopLiveCall();
        }
    });

    // Stop / Barge-in button
    stopBtn.addEventListener('click', () => {
        stopPlayback();
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: 'stop_audio' }));
        }
    });

    // Reset memory
    resetBtn.addEventListener('click', () => {
        if (confirm('Clear AI BFF conversation memory?')) {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ action: 'reset_context' }));
            }
        }
    });

    // Toggle collapsible text bar
    textToggleBtn.addEventListener('click', () => {
        textBar.style.display = (textBar.style.display === 'none') ? 'flex' : 'none';
        if (textBar.style.display === 'flex') textInput.focus();
    });

    // Text bar submission
    sendBtn.addEventListener('click', () => {
        const val = textInput.value.trim();
        if (val) {
            sendTurnText(val);
            textInput.value = '';
        }
    });

    textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const val = textInput.value.trim();
            if (val) {
                sendTurnText(val);
                textInput.value = '';
            }
        }
    });

    // Quick trigger chips
    document.querySelectorAll('.quick-chip').forEach(btn => {
        btn.addEventListener('click', () => {
            const prompt = btn.dataset.prompt;
            if (prompt) sendTurnText(prompt);
        });
    });

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
});
