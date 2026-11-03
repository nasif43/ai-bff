import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Helper to load .env if present
env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_file):
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# API Keys (Loaded from environment variables or .env file)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# Models
GROQ_MODEL = "qwen/qwen3.8-27b"
GROQ_FALLBACK_MODEL = "openai/gpt-oss-120b"
ELEVENLABS_MODEL_ID = "eleven_v4"

# Server configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = int(os.getenv("PORT", 8080))

# Voice configuration mappings
VOICE_PROFILES = {
    "Adam_Stone": {
        "voice_id": "auq43ws1oslv0tO4BDa7",
        "stability": 0.28,
        "similarity_boost": 0.80,
        "style": 0.88,
        "speed": 0.90,
    },
    "Jessica": {
        "voice_id": "cgSgspJ2msm6clMCkdW9",
        "stability": 0.25,
        "similarity_boost": 0.80,
        "style": 0.92,
        "speed": 0.88,
    },
    "Liam": {
        "voice_id": "TX3LPaxmHKxFdv7VOQHJ",
        "stability": 0.28,
        "similarity_boost": 0.80,
        "style": 0.90,
        "speed": 0.90,
    },
    "Laura": {
        "voice_id": "FGY2WhTYpPnrIDTdsKH5",
        "stability": 0.25,
        "similarity_boost": 0.80,
        "style": 0.92,
        "speed": 0.90,
    },
}

# Archetype + Gender to Voice Profile mapping
DEFAULT_VOICE_MAPPING = {
    ("DarkSoul", "M"): "Adam_Stone",
    ("DarkSoul", "F"): "Jessica",
    ("Trickster", "M"): "Liam",
    ("Trickster", "F"): "Laura",
    ("Soother", "M"): "Adam_Stone",
    ("Soother", "F"): "Jessica",
}

VALID_ARCHETYPES = ["DarkSoul", "Trickster", "Soother"]
VALID_ATTITUDES = ["Delulu", "ChronicallyOnline", "VillainEra", "Unbothered"]
VALID_GENDERS = ["M", "F"]
