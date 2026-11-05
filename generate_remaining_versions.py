#!/usr/bin/env python3
"""
Generates the remaining 10 missing gender versions of the AI BFF script
with both MP3 audio and JSON alignment timestamps using ElevenLabs eleven_v4 with-timestamps.
"""

import os
import re
import json
import time
import base64
import requests

API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
if not API_KEY and os.path.exists("11labs_API_KEY.txt"):
    with open("11labs_API_KEY.txt", "r") as f:
        API_KEY = f.read().strip()

BASE_URL = "https://api.elevenlabs.io/v1"
OUTPUT_DIR = "/home/muhts/dev/Codes/kat/ai-bff/audio"
SCRIPT_PATH = "/home/muhts/dev/Codes/kat/ai-bff/script_raw.txt"
MODEL = "eleven_v4"

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
    "Riley_Crush": {
        "voice_id": "hA4zGnmTwX2NQiTRMt7o",
        "stability": 0.36,
        "similarity_boost": 0.75,
        "style": 0.94,
        "speed": 0.85,
    },
}

# 10 Missing Versions:
REMAINING_VERSIONS = [
    # (version_index_in_script, folder_name, prefix, bff_voice_key, bff_gender)
    (3,  "DarkSoul_VillainEra_F",        "DarkSoul_VillainEra",        "Jessica",    "F"),
    (4,  "DarkSoul_Unbothered_F",        "DarkSoul_Unbothered",        "Jessica",    "F"),
    (5,  "Trickster_ChronicallyOnline_F", "Trickster_ChronicallyOnline", "Laura",   "F"),
    (6,  "Trickster_Unbothered_F",       "Trickster_Unbothered",       "Laura",      "F"),
    (7,  "Trickster_Delulu_F",           "Trickster_Delulu",           "Laura",      "F"),
    (8,  "Trickster_VillainEra_F",       "Trickster_VillainEra",       "Laura",      "F"),
    (9,  "Soother_VillainEra_M",         "Soother_VillainEra",         "Adam_Stone", "M"),
    (10, "Soother_ChronicallyOnline_M",  "Soother_ChronicallyOnline",  "Liam",       "M"),
    (11, "Soother_Unbothered_F",         "Soother_Unbothered",         "Jessica",    "F"),
    (12, "Soother_Delulu_M",             "Soother_Delulu",             "Adam_Stone", "M"),
]

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

def strip_emojis(text):
    cleaned = EMOJI_PATTERN.sub(" ", text)
    cleaned = re.sub(r" {2,}", " ", cleaned).strip()
    cleaned = re.sub(r"\s+([.,!?])", r"\1", cleaned)
    return cleaned

def extract_version_sections(script_text):
    markers = list(re.finditer(r'VERSION\s+(\d+)\b', script_text))
    sections = {}
    for i in range(1, 13):
        start = markers[i].start()
        end = markers[i+1].start() if i + 1 < len(markers) else len(script_text)
        sections[i] = script_text[start:end]
    return sections

def parse_section_lines(section_text):
    lines = section_text.splitlines()
    bff_lines = []
    for l in lines:
        m = re.match(r'^(?:\d+\s+)?BFF(?:\s*\(([^)]+)\))?:\s*(.*)', l.strip())
        if m:
            as_info = m.group(1) or ''
            raw_t = m.group(2).strip()
            is_as_m = 'as M' in as_info
            bff_lines.append((raw_t, is_as_m))
    return bff_lines

def build_file_mapping(prefix, bff_gender, bff_lines):
    assert len(bff_lines) == 71, f"Expected 71 lines, got {len(bff_lines)}"
    
    mapping = []
    # 0..9 -> Day 1 lines 1..10
    for i in range(10):
        mapping.append((f"{prefix}_{bff_gender}_{i+1}.mp3", bff_lines[i][0], bff_lines[i][1]))
    # 10..18 -> Week 2 lines 11..19
    for i in range(10, 19):
        mapping.append((f"{prefix}_{bff_gender}_{i+1}.mp3", bff_lines[i][0], bff_lines[i][1]))
    # 19, 20 -> Vote 1 (20_Y, 20_N)
    mapping.append((f"{prefix}_{bff_gender}_20_Y.mp3", bff_lines[19][0], bff_lines[19][1]))
    mapping.append((f"{prefix}_{bff_gender}_20_N.mp3", bff_lines[20][0], bff_lines[20][1]))
    # 21..25 -> Week 3 lines 21..25
    for i in range(21, 26):
        mapping.append((f"{prefix}_{bff_gender}_{i}.mp3", bff_lines[i][0], bff_lines[i][1]))
    # 26 -> Vote 2 YES (Crush line)
    mapping.append((f"{prefix}_F_26_Y.mp3", bff_lines[26][0], True))
    # 27 -> Vote 2 NO
    mapping.append((f"{prefix}_{bff_gender}_26_N.mp3", bff_lines[27][0], False))
    # 28, 29 -> Practice 27, 28
    mapping.append((f"{prefix}_{bff_gender}_27.mp3", bff_lines[28][0], False))
    mapping.append((f"{prefix}_{bff_gender}_28.mp3", bff_lines[29][0], False))
    # 30, 31, 32 -> Practice as M 29, 30, 31 (Crush lines)
    mapping.append((f"{prefix}_F_29.mp3", bff_lines[30][0], True))
    mapping.append((f"{prefix}_F_30.mp3", bff_lines[31][0], True))
    mapping.append((f"{prefix}_F_31.mp3", bff_lines[32][0], True))
    # 33 -> 32
    mapping.append((f"{prefix}_{bff_gender}_32.mp3", bff_lines[33][0], False))
    # 34..40 -> Week 4 lines 33..39
    for i in range(34, 41):
        mapping.append((f"{prefix}_{bff_gender}_{i-1}.mp3", bff_lines[i][0], False))
    # 41 -> Week 5 line 40
    mapping.append((f"{prefix}_{bff_gender}_40.mp3", bff_lines[41][0], False))
    # 42..48 -> Vote 3 YES (41_Y..47_Y)
    for idx, line_idx in enumerate(range(42, 49)):
        mapping.append((f"{prefix}_{bff_gender}_{41+idx}_Y.mp3", bff_lines[line_idx][0], False))
    # 49..56 -> Vote 3 NO (43_N..50_N)
    for idx, line_idx in enumerate(range(49, 57)):
        mapping.append((f"{prefix}_{bff_gender}_{43+idx}_N.mp3", bff_lines[line_idx][0], False))
    # 57 -> Week 6 line 52
    mapping.append((f"{prefix}_{bff_gender}_52.mp3", bff_lines[57][0], False))
    # 58, 59, 60 -> Week 7 lines 53, 54, 55
    for idx, line_idx in enumerate(range(58, 61)):
        mapping.append((f"{prefix}_{bff_gender}_{53+idx}.mp3", bff_lines[line_idx][0], False))
    # 61 -> 56 ("do you want to pause our conversation and have dinner?")
    mapping.append((f"{prefix}_{bff_gender}_56.mp3", bff_lines[61][0], False))
    # 62, 63 -> Vote 4 YES (56_Y, 57_Y)
    mapping.append((f"{prefix}_{bff_gender}_56_Y.mp3", bff_lines[62][0], False))
    mapping.append((f"{prefix}_{bff_gender}_57_Y.mp3", bff_lines[63][0], False))
    # 64, 65, 66 -> Vote 4 NO (57_N, 58_N, 59_N)
    mapping.append((f"{prefix}_{bff_gender}_57_N.mp3", bff_lines[64][0], False))
    mapping.append((f"{prefix}_{bff_gender}_58_N.mp3", bff_lines[65][0], False))
    mapping.append((f"{prefix}_{bff_gender}_59_N.mp3", bff_lines[66][0], False))
    # 67, 68 -> Paywall lines 60, 61
    mapping.append((f"{prefix}_{bff_gender}_60.mp3", bff_lines[67][0], False))
    mapping.append((f"{prefix}_{bff_gender}_61.mp3", bff_lines[68][0], False))
    # 69, 70 -> Week 8 lines 62, 63
    mapping.append((f"{prefix}_{bff_gender}_62.mp3", bff_lines[69][0], False))
    mapping.append((f"{prefix}_{bff_gender}_63.mp3", bff_lines[70][0], False))
    
    return mapping

def extract_word_timestamps(alignment):
    chars = alignment.get("characters", [])
    starts = alignment.get("character_start_times_seconds", [])
    ends = alignment.get("character_end_times_seconds", [])
    words = []
    current_word = ""
    w_start = None
    for i, ch in enumerate(chars):
        if ch.isspace() or i == len(chars) - 1:
            if not ch.isspace():
                current_word += ch
            if current_word:
                w_end = ends[i] if i < len(ends) else (starts[i] + 0.1 if i < len(starts) else 0.0)
                words.append({
                    "word": current_word,
                    "start": round(w_start if w_start is not None else 0.0, 3),
                    "end": round(w_end, 3)
                })
                current_word = ""
                w_start = None
        else:
            if w_start is None and i < len(starts):
                w_start = starts[i]
            current_word += ch
    total_dur = max(ends) if ends else 0.0
    return words, round(total_dur, 3)

def generate_audio_and_timestamps(text, voice_cfg, out_mp3_path, out_json_path):
    clean = strip_emojis(text)
    if not clean.strip():
        return False
        
    url = f"{BASE_URL}/text-to-speech/{voice_cfg['voice_id']}/with-timestamps"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY,
    }
    payload = {
        "text": clean,
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
                data = r.json()
                audio_bytes = base64.b64decode(data.get("audio_base64", ""))
                with open(out_mp3_path, "wb") as f:
                    f.write(audio_bytes)
                
                alignment = data.get("alignment", {})
                words, total_dur = extract_word_timestamps(alignment)
                
                with open(out_json_path, "w") as f:
                    json.dump({
                        "text": clean,
                        "duration": total_dur,
                        "timestamps": words
                    }, f, indent=2)
                return True
            elif r.status_code == 429:
                wait = 20 * (attempt + 1)
                print(f"    [RATE LIMIT] Waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    [ERROR] HTTP {r.status_code}: {r.text[:120]}")
                return False
        except Exception as e:
            print(f"    [EXCEPTION] {e}")
            time.sleep(5)
    return False

def main():
    with open(SCRIPT_PATH) as f:
        script_text = f.read()
        
    sections = extract_version_sections(script_text)
    
    print("=" * 70)
    print("AI BFF AUDIO & TIMESTAMPS GENERATOR — REMAINING 10 VERSIONS")
    print(f"Model: {MODEL} (with-timestamps) | Output: {OUTPUT_DIR}")
    print("=" * 70)
    
    for v_num, folder_name, prefix, voice_key, bff_gender in REMAINING_VERSIONS:
        folder_path = os.path.join(OUTPUT_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        bff_voice = VOICE_PROFILES[voice_key]
        riley_voice = VOICE_PROFILES["Riley_Crush"]
        
        section_text = sections[v_num]
        bff_lines = parse_section_lines(section_text)
        mapping = build_file_mapping(prefix, bff_gender, bff_lines)
        
        print(f"\n[{v_num}/12] Generating: {folder_name} (Voice: {voice_key}, Gender: {bff_gender}, Lines: {len(mapping)})")
        
        for idx, (filename, text, is_as_m) in enumerate(mapping, 1):
            out_mp3 = os.path.join(folder_path, filename)
            out_json = os.path.join(folder_path, filename.replace(".mp3", ".json"))
            
            # Check if both mp3 and json exist
            if os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 1000 and os.path.exists(out_json):
                print(f"  [{idx:02d}/{len(mapping)}] SKIP: {filename}")
                continue
                
            voice_cfg = riley_voice if is_as_m else bff_voice
            print(f"  [{idx:02d}/{len(mapping)}] GENERATING: {filename} ({voice_cfg.get('voice_id')[:8]}...): {text[:45]}...")
            success = generate_audio_and_timestamps(text, voice_cfg, out_mp3, out_json)
            if not success:
                print(f"    FAILED: {filename}")
            time.sleep(0.3)

if __name__ == "__main__":
    main()
