#!/usr/bin/env python3
"""
Generates JSON timestamp alignment files for any existing MP3s in audio/
that do not yet have a matching .json file, using Groq Whisper word timestamps.
"""

import os
import glob
import json
import time
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if not GROQ_API_KEY and os.path.exists("liveAiBff/.env"):
    with open("liveAiBff/.env", "r") as f:
        for line in f:
            if line.startswith("GROQ_API_KEY="):
                GROQ_API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
AUDIO_DIR = "/home/muhts/dev/Codes/kat/ai-bff/audio"

def generate_timestamp_for_file(mp3_path):
    json_path = mp3_path.replace(".mp3", ".json")
    if os.path.exists(json_path) and os.path.getsize(json_path) > 10:
        return True

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    for attempt in range(3):
        try:
            with open(mp3_path, "rb") as f:
                files = {"file": (os.path.basename(mp3_path), f, "audio/mpeg")}
                data = {
                    "model": "whisper-large-v3",
                    "response_format": "verbose_json",
                    "timestamp_granularities[]": "word",
                }
                r = requests.post(url, headers=headers, files=files, data=data, timeout=30)
                if r.status_code == 200:
                    res = r.json()
                    words = res.get("words", [])
                    formatted_timestamps = [
                        {
                            "word": w.get("word", "").strip(),
                            "start": round(w.get("start", 0.0), 3),
                            "end": round(w.get("end", 0.0), 3),
                        }
                        for w in words
                    ]
                    payload = {
                        "text": res.get("text", "").strip(),
                        "duration": round(res.get("duration", 0.0), 3),
                        "timestamps": formatted_timestamps,
                    }
                    with open(json_path, "w") as out_f:
                        json.dump(payload, out_f, indent=2)
                    return True
                elif r.status_code == 429:
                    time.sleep(10)
                else:
                    print(f"  [ERROR] {os.path.basename(mp3_path)}: HTTP {r.status_code}")
                    return False
        except Exception as e:
            print(f"  [EXCEPTION] {e}")
            time.sleep(3)
    return False

def main():
    mp3_files = sorted(glob.glob(f"{AUDIO_DIR}/*/*.mp3"))
    print(f"Total MP3 files found in audio/: {len(mp3_files)}")
    
    missing = [f for f in mp3_files if not os.path.exists(f.replace(".mp3", ".json"))]
    print(f"Files missing JSON timestamps: {len(missing)}")

    for idx, f in enumerate(missing, 1):
        name = os.path.basename(f)
        parent = os.path.basename(os.path.dirname(f))
        print(f"[{idx}/{len(missing)}] {parent}/{name}")
        generate_timestamp_for_file(f)
        time.sleep(0.1)

if __name__ == "__main__":
    main()
