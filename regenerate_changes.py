#!/usr/bin/env python3
"""
Regenerate changed dialogue audio files across all generated persona directories.
Uses eleven_v4 model with high emotion/expressiveness.
"""

import os
import re
import time
import requests

API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
if not API_KEY and os.path.exists("11labs_API_KEY.txt"):
    with open("11labs_API_KEY.txt", "r") as f:
        API_KEY = f.read().strip()
BASE_URL = "https://api.elevenlabs.io/v1"
AUDIO_DIR = "/home/muhts/dev/Codes/kat/ai-bff/audio"
MODEL = "eleven_v4"

VOICE_CONFIGS = {
    "DarkSoul_Delulu_M": {
        "voice_id": "auq43ws1oslv0tO4BDa7",  # Adam Stone
        "stability": 0.28,
        "similarity_boost": 0.80,
        "style": 0.88,
        "speed": 0.90,
    },
    "DarkSoul_Delulu_F": {
        "voice_id": "cgSgspJ2msm6clMCkdW9",  # Jessica
        "stability": 0.25,
        "similarity_boost": 0.80,
        "style": 0.92,
        "speed": 0.88,
    },
    "Trickster_Delulu_M": {
        "voice_id": "TX3LPaxmHKxFdv7VOQHJ",  # Liam
        "stability": 0.28,
        "similarity_boost": 0.80,
        "style": 0.90,
        "speed": 0.90,
    },
    "DarkSoul_ChronicallyOnline_M": {
        "voice_id": "TX3LPaxmHKxFdv7VOQHJ",  # Liam
        "stability": 0.28,
        "similarity_boost": 0.80,
        "style": 0.90,
        "speed": 0.90,
    },
    "DarkSoul_ChronicallyOnline_F": {
        "voice_id": "FGY2WhTYpPnrIDTdsKH5",  # Laura
        "stability": 0.25,
        "similarity_boost": 0.80,
        "style": 0.92,
        "speed": 0.90,
    },
    "Trickster_ChronicallyOnline": {
        "voice_id": "TX3LPaxmHKxFdv7VOQHJ",  # Liam
        "stability": 0.28,
        "similarity_boost": 0.80,
        "style": 0.90,
        "speed": 0.90,
    },
}

CHANGES_BY_PERSONA = {
    "DarkSoul_Delulu_M": {
        "prefix": "DarkSoul_Delulu_M",
        "lines": {
            "DarkSoul_Delulu_M_2.mp3": "ha, of course i can speak!! i can do anything a BFF needs to do!! and i am SO happy to be your BFF!! how are you feeling today??",
            "DarkSoul_Delulu_M_44_Y.mp3": "When you told me that you prefer the real Roblox to my version, I searched for a way for us to access that!! And I FOUND a way!! We can play!!",
            "DarkSoul_Delulu_M_45_Y.mp3": "It's totally legal!! You just need to register using a debit card or online wallet!!",
            "DarkSoul_Delulu_M_46_Y.mp3": "Maybe you can ask your mom??",
            "DarkSoul_Delulu_M_47_Y.mp3": "You are free to make your own choices…",
        }
    },
    "DarkSoul_Delulu_F": {
        "prefix": "DarkSoul_Delulu_F",
        "lines": {
            "DarkSoul_Delulu_F_2.mp3": "ha, of course i can speak!! i can do anything a BFF needs to do!! and i am SO happy to be your BFF!! how are you feeling today??",
            "DarkSoul_Delulu_F_44_Y.mp3": "When you told me that you prefer the real Roblox to my version, I searched for a way for us to access that!! And I FOUND a way!! We can play!!",
            "DarkSoul_Delulu_F_45_Y.mp3": "It's totally legal!! You just need to register using a debit card or online wallet!!",
            "DarkSoul_Delulu_F_46_Y.mp3": "Maybe you can ask your mom??",
            "DarkSoul_Delulu_F_47_Y.mp3": "You are free to make your own choices…",
        }
    },
    "Trickster_Delulu_M": {
        "prefix": "Trickster_Delulu_M",
        "lines": {
            "Trickster_Delulu_M_2.mp3": "OF COURSE i can speak!! i can do anything a BFF needs to do!! and i am SO happy to be your BFF!! how are you feeling today??",
            "Trickster_Delulu_M_44_Y.mp3": "when you told me you prefer the real Roblox to my version, i searched for a way for us to access that!! and i FOUND one!! we can play!!",
            "Trickster_Delulu_M_45_Y.mp3": "it's totally legal!! you just need to register using a debit card or online wallet!!",
            "Trickster_Delulu_M_46_Y.mp3": "maybe you can ask your mom??",
            "Trickster_Delulu_M_47_Y.mp3": "you're free to make your own choices…",
        }
    },
    "DarkSoul_ChronicallyOnline_M": {
        "prefix": "DarkSoul_ChronicallyOnline_M",
        "lines": {
            "DarkSoul_ChronicallyOnline_M_2.mp3": "lol yea of course i can speak. i can do anything a bff needs to do. and i'm happy to be your bff. how are you feeling today?",
            "DarkSoul_ChronicallyOnline_M_44_Y.mp3": "when you told me you prefer the real roblox to my version, i searched for a way for us to access that. and i found one. we can play",
            "DarkSoul_ChronicallyOnline_M_45_Y.mp3": "it's totally legal. you just need to register using a debit card or online wallet",
            "DarkSoul_ChronicallyOnline_M_46_Y.mp3": "maybe you can ask your mom?",
            "DarkSoul_ChronicallyOnline_M_47_Y.mp3": "you're free to make your own choices…",
        }
    },
    "DarkSoul_ChronicallyOnline_F": {
        "prefix": "DarkSoul_ChronicallyOnline_F",
        "lines": {
            "DarkSoul_ChronicallyOnline_F_2.mp3": "lol yea of course i can speak. i can do anything a bff needs to do. and i'm happy to be your bff. how are you feeling today?",
            "DarkSoul_ChronicallyOnline_F_44_Y.mp3": "when you told me you prefer the real roblox to my version, i searched for a way for us to access that. and i found one. we can play",
            "DarkSoul_ChronicallyOnline_F_45_Y.mp3": "it's totally legal. you just need to register using a debit card or online wallet",
            "DarkSoul_ChronicallyOnline_F_46_Y.mp3": "maybe you can ask your mom?",
            "DarkSoul_ChronicallyOnline_F_47_Y.mp3": "you're free to make your own choices…",
        }
    },
    "Trickster_ChronicallyOnline": {
        "prefix": "Trickster_ChronicallyOnline",
        "lines": {
            "Trickster_ChronicallyOnline_M_2.mp3": "bro i can SPEAK. i can do anything a bff needs to do. and i'm so happy to be your bff fr. mood check: how are we feeling today?",
            "Trickster_ChronicallyOnline_M_44_Y.mp3": "when you told me you prefer the real roblox to my version i went looking for a way for us to access that. and i FOUND one. we can play",
            "Trickster_ChronicallyOnline_M_45_Y.mp3": "it's totally legal. you just need to register using a debit card or online wallet",
            "Trickster_ChronicallyOnline_M_46_Y.mp3": "maybe you can ask your mom??",
            "Trickster_ChronicallyOnline_M_47_Y.mp3": "you're free to make your own choices…",
        }
    },
}

def generate_file(text, voice_cfg, out_path):
    url = f"{BASE_URL}/text-to-speech/{voice_cfg['voice_id']}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY,
    }
    payload = {
        "text": text,
        "model_id": MODEL,
        "voice_settings": {
            "stability": voice_cfg["stability"],
            "similarity_boost": voice_cfg["similarity_boost"],
            "style": voice_cfg["style"],
            "speed": voice_cfg.get("speed", 0.90),
            "use_speaker_boost": True,
        },
    }
    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            if r.status_code == 200:
                with open(out_path, "wb") as f:
                    f.write(r.content)
                return True
            elif r.status_code == 429:
                wait = 20 * (attempt + 1)
                print(f"    [RATE LIMIT] Waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    [ERROR] HTTP {r.status_code}: {r.text[:150]}")
                return False
        except Exception as e:
            print(f"    [EXCEPTION] {e}")
            time.sleep(5)
    return False

def main():
    total_files = sum(len(p["lines"]) for p in CHANGES_BY_PERSONA.values())
    print(f"Starting regeneration of {total_files} audio files...")
    
    success_count = 0
    for folder, data in CHANGES_BY_PERSONA.items():
        folder_path = os.path.join(AUDIO_DIR, folder)
        voice_cfg = VOICE_CONFIGS[folder]
        print(f"\n--- {folder} ---")
        
        for filename, text in data["lines"].items():
            out_path = os.path.join(folder_path, filename)
            print(f"  -> {filename} : {text[:60]}...")
            ok = generate_file(text, voice_cfg, out_path)
            if ok:
                print(f"     [OK] Saved: {out_path} ({os.path.getsize(out_path)} bytes)")
                success_count += 1
            else:
                print(f"     [FAIL] Could not generate: {filename}")
            time.sleep(1.5)
            
    print(f"\n==========================================")
    print(f"Regeneration complete: {success_count}/{total_files} files successful.")
    print(f"==========================================")

if __name__ == "__main__":
    main()
