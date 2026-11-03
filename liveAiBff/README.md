# Live AI BFF - 3D Avatar & Lip-Sync Integration Guide

Real-time interaction engine for the AI BFF stage play. This service orchestrates speech-to-text input, dynamic persona generation via Groq LLM, and ElevenLabs expressive voice synthesis (`eleven_v4`) with word-level alignment timestamps for driving real-time 3D facial animation, lip-sync, and subtitles.

---

## 1. Quick Start & Setup

### Prerequisites
- Python 3.10+ (tested on Python 3.11 / 3.12 / 3.13)
- API Keys for Groq Cloud and ElevenLabs

### Setup Instructions

1. **Clone the repository and enter directory:**
   ```bash
   git clone git@github.com:nasif43/ai-bff.git
   cd ai-bff/liveAiBff
   ```

2. **Configure Environment Keys:**
   Create a `.env` file from the provided template:
   ```bash
   cp .env.example .env
   ```
   Open `.env` in your editor and insert the API keys:
   ```env
   GROQ_API_KEY=gsk_...
   ELEVENLABS_API_KEY=sk_...
   PORT=8080
   ```

3. **Install Dependencies & Start the Server:**
   Using the automatic startup script (creates `venv` and installs packages automatically):
   ```bash
   chmod +x run.sh
   ./run.sh
   ```
   *Or manually via pip:*
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python3 server.py
   ```

The server binds to `0.0.0.0:8080`.
- **Web Controller UI:** `http://localhost:8080` (or `http://<LAN_IP>:8080` on mobile)
- **WebSocket Endpoint:** `ws://<HOST>:8080/ws`
- **Audio Asset Delivery:** `http://<HOST>:8080/audio/<filename>.mp3`

---

## 2. WebSocket Protocol (`/ws`)

Connect any client (Three.js, Unity, Unreal, Godot, or Web) to `ws://<HOST>:8080/ws`. All connected clients receive broadcasts simultaneously.

### A. Client to Server Messages

#### 1. Configure Persona & Voice
Change the active archetype, attitude modifier, and voice profile at any time:
```json
{
  "action": "set_config",
  "archetype": "Trickster",
  "attitude": "ChronicallyOnline",
  "gender": "M"
}
```
- **`archetype`**: `"DarkSoul"` | `"Trickster"` | `"Soother"`
- **`attitude`**: `"Delulu"` | `"ChronicallyOnline"` | `"VillainEra"` | `"Unbothered"`
- **`gender`**: `"M"` | `"F"`

#### 2. Send Spoken / Text Input
Trigger a live response turn:
```json
{
  "text": "Hey bestie, I think I failed my exam."
}
```

#### 3. Interrupt / Stop Playback
Immediately stops current speech and signals all visualizers:
```json
{
  "action": "stop_audio"
}
```

#### 4. Reset Conversation Memory
Clears chat context:
```json
{
  "action": "reset_context"
}
```

---

### B. Server to Client Events

#### 1. Turn Complete (`turn_complete`)
Dispatched immediately when LLM generation and voice synthesis are complete. Contains full lip-sync alignment and facial emotion tags.

```json
{
  "event": "turn_complete",
  "user_text": "Hey bestie, I think I failed my exam.",
  "text": "Bro, you didn't fail, you just achieved peak skibidi status and unlocked the 'L' achievement no cap.",
  "emotion": "smirk",
  "audio_url": "/audio/turn_1793691526134.mp3",
  "duration": 4.82,
  "timestamps": [
    {"word": "Bro,", "start": 0.0, "end": 0.42},
    {"word": "you", "start": 0.42, "end": 0.58},
    {"word": "didn't", "start": 0.58, "end": 0.86},
    {"word": "fail,", "start": 0.86, "end": 1.34},
    {"word": "you", "start": 1.34, "end": 1.48},
    {"word": "just", "start": 1.48, "end": 1.72},
    {"word": "achieved", "start": 1.72, "end": 2.15}
  ],
  "archetype": "Trickster",
  "attitude": "ChronicallyOnline",
  "gender": "M"
}
```

#### 2. Pipeline Status (`status`)
Sent during intermediary processing phases:
```json
{ "event": "status", "state": "generating_llm", "user_text": "..." }
{ "event": "status", "state": "generating_tts", "text": "...", "emotion": "smirk" }
```

#### 3. Audio Stop Notification (`audio_stopped`)
Sent when an audio stop or interrupt is initiated:
```json
{ "event": "audio_stopped" }
```

---

## 3. Lip-Sync & Viseme Synchronization Guide

### Synchronizing Word Boundaries
Each entry in `timestamps` contains exact start and end times in seconds relative to the audio file:
```json
{"word": "fail,", "start": 0.86, "end": 1.34}
```

To drive lip-sync in your animation loop:
```javascript
const audio = new Audio("http://localhost:8080" + payload.audio_url);
audio.play();

function onAnimationFrame() {
    const t = audio.currentTime;
    
    // Find active word
    const activeWord = payload.timestamps.find(w => t >= w.start && t <= w.end);
    if (activeWord) {
        // Drive mouth flap / viseme targets based on active word / phonemes
        avatar.setMouthOpen(0.65);
    } else {
        avatar.setMouthOpen(0.0);
    }
    
    if (!audio.paused && !audio.ended) {
        requestAnimationFrame(onAnimationFrame);
    }
}
requestAnimationFrame(onAnimationFrame);
```

### Emotion Tag Mapping
The `emotion` field specifies the character's facial expression and postural demeanor for the turn:

| Emotion Tag | Recommended Blendshapes / Facial Morphs |
| :--- | :--- |
| `smirk` | Asymmetric mouth corner raise, squinted eye, eyebrow arch |
| `sarcastic` | Eyebrow raise, slight head tilt, smirk/scoff mouth shape |
| `comforting` | Soft smile, relaxed eyelids, head tilt, warm gaze |
| `delusional` | Wide eyes, intense arched brows, wide eager smile |
| `villainous` | Brow furrow (corrugator), narrowed eyelids, sinister grin |
| `unbothered` | Half-closed eyelids, flat neutral mouth, slack posture |
| `dramatic` | Wide eyes, dropped jaw, high raised brows |
| `alarmed` | Dilated pupils, wide eyes, raised brows, mouth open |
| `neutral` | Default relaxed resting expression |

---

## 4. Architecture & Configuration Reference

- **`config.py`**: API keys, network host/port, ElevenLabs voice profile configurations, and archetype voice mappings.
- **`prompts.py`**: Persona matrix (3 Archetypes $\times$ 4 Attitudes) and stage dialogue formatting rules.
- **`groq_engine.py`**: Handles fast Groq inference (`qwen/qwen3.8-27b` with sub-second latency), emotion tag parsing, and regex sanitization of stage text.
- **`tts_engine.py`**: Interfaces with ElevenLabs `with-timestamps` API (`eleven_v4`) and calculates word-level alignment arrays.
- **`server.py`**: Asynchronous `aiohttp` WebSocket server broadcasting turns and serving static and audio assets.
- **`static/`**: Mobile controller web client with Web Speech API input, archetype selectors, and karaoke subtitle synchronization.
