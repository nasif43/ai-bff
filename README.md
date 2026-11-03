# AI BFF - Interactive Theatrical Voice & Avatar Engine

This repository hosts the script, audio generation pipelines, and live interactive off-script dialogue engine for the **AI BFF** theatrical production.

## Repository Contents

- **`liveAiBff/`**: Real-time live interaction engine (Groq LLM + ElevenLabs `eleven_v4` TTS + WebSocket server + Web controller). See [`liveAiBff/README.md`](./liveAiBff/README.md) for 3D animation, avatar lip-sync, and viseme integration documentation.
- **`generate_all_12_versions.py`**: Audio generation pipeline for the 12 full script archetypes.
- **`script_raw.txt`**: Complete master script covering all 12 archetype combinations.
- **`script.docx` / `script.html`**: Formatted production script documentation.

## Getting Started

To run the live interactive engine:
```bash
cd liveAiBff
cp .env.example .env
# Edit .env and supply your GROQ_API_KEY and ELEVENLABS_API_KEY
chmod +x run.sh
./run.sh
```
