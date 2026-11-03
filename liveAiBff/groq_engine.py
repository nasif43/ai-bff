"""
Groq LLM Engine for Live AI BFF.
Handles chat completions, emotion tag extraction, and stage dialogue cleaning.
"""

import re
import requests
from typing import Dict, List, Tuple
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_FALLBACK_MODEL
from prompts import get_system_prompt

# Regex for emotion tag extraction
EMOTION_TAG_PATTERN = re.compile(r"^\[EMOTION:\s*([a-zA-Z_]+)\]", re.IGNORECASE)

# Emoji stripping regex
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\u2600-\u26FF"
    "\u2700-\u27BF"
    "\U0001F1E0-\U0001F1FF"
    "\u200d"
    "\uFE0F"
    "\u20E3"
    "]+",
    flags=re.UNICODE,
)

class GroqEngine:
    def __init__(self, api_key: str = GROQ_API_KEY):
        self.api_key = api_key
        self.url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def clean_dialogue(self, raw_text: str) -> Tuple[str, str]:
        """
        Extracts emotion tag and strips non-verbal markers (asterisks, brackets, emojis).
        Returns: (cleaned_text, emotion)
        """
        text = raw_text.strip()
        emotion = "neutral"

        # Check for [EMOTION: ...] tag
        match = EMOTION_TAG_PATTERN.search(text)
        if match:
            emotion = match.group(1).lower().strip()
            text = text[match.end():].strip()

        # Strip remaining bracketed notes e.g. [laughs] or (sighs)
        text = re.sub(r"\[.*?\]", "", text)
        text = re.sub(r"\(.*?\)", "", text)

        # Strip asterisks e.g. *rolls eyes*
        text = re.sub(r"\*.*?\*", "", text)
        text = re.sub(r"\*", "", text)

        # Strip emojis
        text = EMOJI_PATTERN.sub(" ", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        return text, emotion

    def generate_turn(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        archetype: str,
        attitude: str,
    ) -> Tuple[str, str]:
        """
        Sends conversation with system prompt to Groq.
        Returns: (spoken_text, emotion_tag)
        """
        system_prompt = get_system_prompt(archetype, attitude)
        messages = [{"role": "system", "content": system_prompt}] + conversation_history + [
            {"role": "user", "content": user_message}
        ]

        # Primary attempt with fast model
        models_to_try = [GROQ_MODEL, GROQ_FALLBACK_MODEL]

        last_error = None
        for model in models_to_try:
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": 150,
                    "temperature": 0.85,
                }
                response = requests.post(
                    self.url,
                    headers=self.headers,
                    json=payload,
                    timeout=8,
                )
                if response.status_code == 200:
                    data = response.json()
                    raw_reply = data["choices"][0]["message"].get("content", "")
                    if raw_reply.strip():
                        cleaned_text, emotion = self.clean_dialogue(raw_reply)
                        return cleaned_text, emotion
                else:
                    last_error = response.text
                    print(f"[GroqEngine] Model {model} returned status {response.status_code}: {response.text}")
            except Exception as e:
                last_error = str(e)
                print(f"[GroqEngine] Exception querying {model}: {e}")

        # Fallback response if all API calls failed
        fallback_text = "I heard you, but my network glitched for a second. Say that again."
        return fallback_text, "alarmed"

    def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.webm") -> str:
        """
        Transcribes audio bytes using Groq Whisper.
        """
        stt_url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        files = {"file": (filename, audio_bytes, "audio/webm")}
        data = {"model": "whisper-large-v3-turbo"}
        try:
            res = requests.post(stt_url, headers=headers, files=files, data=data, timeout=10)
            if res.status_code == 200:
                return res.json().get("text", "").strip()
            print(f"[GroqEngine] STT error {res.status_code}: {res.text}")
        except Exception as e:
            print(f"[GroqEngine] STT exception: {e}")
        return ""

