"""
ElevenLabs TTS Engine for Live AI BFF.
Uses eleven_v4 with word-level timestamps and character alignment extraction.
"""

import os
import time
import base64
import requests
from typing import Dict, List, Tuple, Any, Optional
from config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_MODEL_ID,
    VOICE_PROFILES,
    DEFAULT_VOICE_MAPPING,
    AUDIO_DIR,
)

class TTSEngine:
    def __init__(self, api_key: str = ELEVENLABS_API_KEY):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"

    def get_voice_config(self, archetype: str, gender: str) -> Tuple[str, Dict[str, Any]]:
        """
        Resolves voice profile parameters based on archetype and gender.
        """
        profile_name = DEFAULT_VOICE_MAPPING.get((archetype, gender), "Adam_Stone")
        profile = VOICE_PROFILES.get(profile_name, VOICE_PROFILES["Adam_Stone"])
        return profile["voice_id"], profile

    def convert_with_timestamps(
        self,
        text: str,
        archetype: str = "DarkSoul",
        gender: str = "M",
    ) -> Dict[str, Any]:
        """
        Converts text to speech and generates word-level timestamps.

        Returns a dictionary containing:
        - audio_path: Local filepath on disk
        - audio_url: Web path for streaming
        - timestamps: List of {"word": str, "start": float, "end": float}
        - duration: Total duration in seconds
        """
        if not text.strip():
            return {"error": "Empty text provided"}

        voice_id, profile = self.get_voice_config(archetype, gender)
        url = f"{self.base_url}/text-to-speech/{voice_id}/with-timestamps"

        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {
            "text": text,
            "model_id": ELEVENLABS_MODEL_ID,
            "voice_settings": {
                "stability": profile.get("stability", 0.28),
                "similarity_boost": profile.get("similarity_boost", 0.80),
                "style": profile.get("style", 0.88),
                "use_speaker_boost": True,
            },
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code != 200:
                print(f"[TTSEngine] ElevenLabs error {response.status_code}: {response.text}")
                return {"error": f"ElevenLabs API failed with status {response.status_code}"}

            data = response.json()
            audio_bytes = base64.b64decode(data.get("audio_base64", ""))

            # Save MP3 file
            turn_id = f"turn_{int(time.time() * 1000)}"
            filename = f"{turn_id}.mp3"
            filepath = os.path.join(AUDIO_DIR, filename)

            with open(filepath, "wb") as f:
                f.write(audio_bytes)

            # Build word-level timestamps from character alignment
            word_timestamps: List[Dict[str, Any]] = []
            alignment = data.get("alignment", {})
            chars = alignment.get("characters", [])
            start_times = alignment.get("character_start_times_seconds", [])
            end_times = alignment.get("character_end_times_seconds", [])

            current_word = ""
            word_start: Optional[float] = None
            total_duration = 0.0

            for i, ch in enumerate(chars):
                if i < len(end_times):
                    total_duration = max(total_duration, end_times[i])

                if ch.isspace() or i == len(chars) - 1:
                    if not ch.isspace():
                        current_word += ch

                    if current_word:
                        word_end = end_times[i] if i < len(end_times) else (
                            start_times[i] + 0.1 if i < len(start_times) else 0.0
                        )
                        word_timestamps.append({
                            "word": current_word,
                            "start": round(word_start if word_start is not None else 0.0, 3),
                            "end": round(word_end, 3),
                        })
                        current_word = ""
                        word_start = None
                else:
                    if word_start is None and i < len(start_times):
                        word_start = start_times[i]
                    current_word += ch

            # Save timestamps JSON file alongside MP3
            json_filename = f"{turn_id}.json"
            json_filepath = os.path.join(AUDIO_DIR, json_filename)
            with open(json_filepath, "w") as f:
                json.dump({
                    "text": text,
                    "duration": round(total_duration, 3),
                    "timestamps": word_timestamps,
                    "archetype": archetype,
                    "gender": gender,
                }, f, indent=2)

            return {
                "audio_path": filepath,
                "audio_url": f"/audio/{filename}",
                "timestamps": word_timestamps,
                "duration": round(total_duration, 3),
            }

        except Exception as e:
            print(f"[TTSEngine] Exception generating TTS: {e}")
            return {"error": str(e)}
