# Live AI BFF - 3D Avatar & Lip-Sync Integration Guide

Real-time interaction engine for the AI BFF stage play. This service orchestrates speech-to-text input, dynamic persona generation via Groq LLM, and ElevenLabs expressive voice synthesis (`eleven_v4`) with word-level alignment timestamps for driving real-time 3D facial animation, lip-sync, and stage audio playback.

---

## 1. Quick Start & Setup

### Prerequisites
- Python 3.10+
- Groq Cloud API Key & ElevenLabs API Key

### Installation & Startup
```bash
git clone git@github.com:nasif43/ai-bff.git
cd ai-bff/liveAiBff
cp .env.example .env
# Edit .env and supply your keys:
# GROQ_API_KEY=gsk_...
# ELEVENLABS_API_KEY=sk_...
chmod +x run.sh
./run.sh
```

The server automatically starts a secure Cloudflare Tunnel:
- **Phone Controller UI:** `https://<tunnel-id>.trycloudflare.com` (or `http://localhost:8080`)
- **Stage 3D Client WebSocket:** `ws://localhost:8080/ws` (or `wss://<tunnel-id>.trycloudflare.com/ws`)
- **Audio Asset Delivery:** `http://localhost:8080/audio/<filename>.mp3`

---

## 2. WebSocket Protocol (`/ws`)

Connect your 3D visualizer, avatar engine (Three.js, Unity, Unreal, Godot), or stage audio client to the WebSocket endpoint. All connected clients receive event broadcasts simultaneously.

### A. Server Broadcast Events

#### 1. Turn Complete (`turn_complete`)
Dispatched immediately when speech generation and voice synthesis are complete. Contains full lip-sync alignment, audio URL, and facial emotion tags.

```json
{
  "event": "turn_complete",
  "user_text": "Yo bro, is this live?",
  "text": "Yes, Shihab, you are bleeding real-time into the void, but do not panic.",
  "emotion": "smirk",
  "audio_url": "/audio/turn_1793692850658.mp3",
  "duration": 4.82,
  "audio_route": "both",
  "timestamps": [
    {"word": "Yes,", "start": 0.0, "end": 0.42},
    {"word": "Shihab,", "start": 0.42, "end": 1.15},
    {"word": "you", "start": 1.15, "end": 1.30},
    {"word": "are", "start": 1.30, "end": 1.48},
    {"word": "bleeding", "start": 1.48, "end": 1.95},
    {"word": "real-time", "start": 1.95, "end": 2.45},
    {"word": "into", "start": 2.45, "end": 2.70},
    {"word": "the", "start": 2.70, "end": 2.85},
    {"word": "void,", "start": 2.85, "end": 3.40}
  ],
  "archetype": "DarkSoul",
  "attitude": "Delulu",
  "gender": "M"
}
```

##### Field Reference:
- **`text`**: Spoken dialogue line (cleaned of stage directions/asterisks).
- **`audio_url`**: Relative path to the synthesized MP3 audio file.
- **`timestamps`**: Array of word objects with exact `start` and `end` times in seconds relative to the audio file.
- **`duration`**: Total duration of the audio in seconds.
- **`emotion`**: Dominant facial expression tag for this turn (`smirk`, `delusional`, `villainous`, `comforting`, `unbothered`, `sarcastic`, `alarmed`, `neutral`).
- **`audio_route`**: Selected audio output destination:
  - `"screen"`: Audio should play **only through the stage screen / sound system** (phone is muted).
  - `"both"`: Audio plays through both the phone and stage screen speakers.
  - `"phone"`: Audio plays only on the actor's phone (screen muted).

#### 2. Pipeline Status (`status`)
Broadcast during intermediate processing steps:
```json
{ "event": "status", "state": "generating_llm", "user_text": "..." }
{ "event": "status", "state": "generating_tts", "text": "...", "emotion": "smirk" }
```

#### 3. Audio Stop / Interrupt (`audio_stopped`)
Broadcast whenever a barge-in interrupt occurs:
```json
{ "event": "audio_stopped" }
```
When this event arrives, stop screen audio playback immediately and reset avatar mouth blendshapes to 0.

---

## 3. Screen / Stage 3D Client Implementation Template

Below is a complete, production-ready JavaScript client for the screen/stage animation machine:

```javascript
const WS_URL = "ws://localhost:8080/ws"; // or wss://<tunnel>.trycloudflare.com/ws
const BASE_HTTP = "http://localhost:8080";

let socket;
let currentAudio = null;
let currentTimestamps = [];
let animFrameId = null;

function connect() {
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
        console.log("[Screen 3D] Connected to Live AI BFF Engine");
    };

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.event === "turn_complete") {
            handleAvatarTurn(data);
        } else if (data.event === "audio_stopped") {
            stopAvatarPlayback();
        }
    };

    socket.onclose = () => {
        console.warn("[Screen 3D] Disconnected. Reconnecting in 2s...");
        setTimeout(connect, 2000);
    };
}

function handleAvatarTurn(turn) {
    // 1. Set character facial expression / blendshape from emotion tag
    setAvatarEmotion(turn.emotion);

    // 2. Play audio through stage speakers (if route is 'screen' or 'both')
    if (turn.audio_route === "screen" || turn.audio_route === "both") {
        if (currentAudio) {
            currentAudio.pause();
        }

        currentAudio = new Audio(BASE_HTTP + turn.audio_url);
        currentAudio.volume = 1.0;
        currentTimestamps = turn.timestamps || [];

        currentAudio.play().then(() => {
            cancelAnimationFrame(animFrameId);
            runLipSyncLoop();
        }).catch(err => {
            console.error("Audio playback error:", err);
        });

        currentAudio.onended = () => {
            stopAvatarPlayback();
        };
    }
}

function runLipSyncLoop() {
    if (currentAudio && !currentAudio.paused && !currentAudio.ended) {
        const currentTime = currentAudio.currentTime;

        // Find active word at this exact millisecond
        const activeWord = currentTimestamps.find(
            w => currentTime >= w.start && currentTime <= w.end
        );

        if (activeWord) {
            // Drive avatar mouth opening / viseme
            // Replace with your 3D engine's morph target (e.g. avatar.morphTargetInfluences[jawOpenIndex] = 0.7)
            setAvatarMouthOpen(0.75);
        } else {
            // Slight pause between words
            setAvatarMouthOpen(0.05);
        }

        animFrameId = requestAnimationFrame(runLipSyncLoop);
    } else {
        setAvatarMouthOpen(0.0);
    }
}

function stopAvatarPlayback() {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    cancelAnimationFrame(animFrameId);
    setAvatarMouthOpen(0.0);
    resetAvatarEmotion();
}

// Stubs for your 3D engine (Three.js / Babylon / Unity WebGL)
function setAvatarMouthOpen(value) {
    // e.g., morphTargets['jawOpen'] = value;
}

function setAvatarEmotion(emotion) {
    // e.g., apply blendshapes for 'smirk', 'villainous', 'comforting', etc.
}

function resetAvatarEmotion() {
    // Reset to neutral resting pose
}

connect();
```

---

## 4. Emotion to Blendshape Mapping Reference

| Emotion Tag | Recommended Blendshapes / Morphs | Character Attitude |
| :--- | :--- | :--- |
| `smirk` | `mouthSmileLeft` (0.8), `eyeSquintLeft` (0.5), `browInnerUp` (0.3) | Cynical, teasing |
| `sarcastic` | `browOuterUpRight` (0.7), `mouthPucker` (0.4), `headTilt` (0.3) | Mocking, deadpan |
| `comforting` | `mouthSmile` (0.5), `browInnerUp` (0.4), `eyeWide` (0.2) | Warm, gentle, reassuring |
| `delusional` | `eyeWide` (0.9), `browInnerUp` (0.7), `mouthSmile` (0.8) | High energy, wide-eyed denial |
| `villainous` | `browDownLeft` (0.9), `browDownRight` (0.9), `mouthFrown` (0.5) | Petty revenge, menacing |
| `unbothered` | `eyeSquint` (0.7), `mouthFlat` (0.6), `browDown` (0.2) | Low energy, deadpan, stoic |
| `dramatic` | `eyeWide` (1.0), `jawOpen` (0.6), `browInnerUp` (0.9) | Over-the-top shock |
| `alarmed` | `eyeWide` (1.0), `jawOpen` (0.8), `browInnerUp` (0.8) | Panicked, defensive |
| `neutral` | Resting pose (all morphs at 0.0) | Default |
