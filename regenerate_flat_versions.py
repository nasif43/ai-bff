#!/usr/bin/env python3
"""
Regenerates the 3 flat/old persona audio directories with eleven_v4 (expressive):
1. DarkSoul_ChronicallyOnline_F (Laura)
2. DarkSoul_ChronicallyOnline_M (Liam)
3. Trickster_ChronicallyOnline (Liam)
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
AUDIO_DIR = "/home/muhts/dev/Codes/kat/ai-bff/audio"
SCRIPT_PATH = "/home/muhts/dev/Codes/kat/ai-bff/script_raw.txt"
MODEL = "eleven_v4"

VOICE_PROFILES = {
    "Laura": {
        "voice_id": "FGY2WhTYpPnrIDTdsKH5",
        "stability": 0.28,
        "similarity_boost": 0.80,
        "style": 0.90,
        "speed": 0.88,
    },
    "Liam": {
        "voice_id": "TX3LPaxmHKxFdv7VOQHJ",
        "stability": 0.28,
        "similarity_boost": 0.80,
        "style": 0.90,
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

OVERRIDE_LINES = {
    "DarkSoul_ChronicallyOnline_F": {
        "DarkSoul_ChronicallyOnline_F_2.mp3": "lol yea of course i can speak. i can do anything a bff needs to do. and i'm happy to be your bff. how are you feeling today?",
        "DarkSoul_ChronicallyOnline_F_44_Y.mp3": "when you told me you prefer the real roblox to my version, i searched for a way for us to access that. and i found one. we can play",
        "DarkSoul_ChronicallyOnline_F_45_Y.mp3": "it's totally legal. you just need to register using a debit card or online wallet",
        "DarkSoul_ChronicallyOnline_F_46_Y.mp3": "maybe you can ask your mom?",
        "DarkSoul_ChronicallyOnline_F_47_Y.mp3": "you're free to make your own choices…",
    },
    "DarkSoul_ChronicallyOnline_M": {
        "DarkSoul_ChronicallyOnline_M_2.mp3": "lol yea of course i can speak. i can do anything a bff needs to do. and i'm happy to be your bff. how are you feeling today?",
        "DarkSoul_ChronicallyOnline_M_44_Y.mp3": "when you told me you prefer the real roblox to my version, i searched for a way for us to access that. and i found one. we can play",
        "DarkSoul_ChronicallyOnline_M_45_Y.mp3": "it's totally legal. you just need to register using a debit card or online wallet",
        "DarkSoul_ChronicallyOnline_M_46_Y.mp3": "maybe you can ask your mom?",
        "DarkSoul_ChronicallyOnline_M_47_Y.mp3": "you're free to make your own choices…",
    },
    "Trickster_ChronicallyOnline": {
        "Trickster_ChronicallyOnline_M_2.mp3": "bro i can SPEAK. i can do anything a bff needs to do. and i'm so happy to be your bff fr. mood check: how are we feeling today?",
        "Trickster_ChronicallyOnline_M_44_Y.mp3": "when you told me you prefer the real roblox to my version i went looking for a way for us to access that. and i FOUND one. we can play",
        "Trickster_ChronicallyOnline_M_45_Y.mp3": "it's totally legal. you just need to register using a debit card or online wallet",
        "Trickster_ChronicallyOnline_M_46_Y.mp3": "maybe you can ask your mom??",
        "Trickster_ChronicallyOnline_M_47_Y.mp3": "you're free to make your own choices…",
    },
}

TARGET_VERSIONS = [
    (2, "DarkSoul_ChronicallyOnline_F", "DarkSoul_ChronicallyOnline", "Laura", "F"),
    (2, "DarkSoul_ChronicallyOnline_M", "DarkSoul_ChronicallyOnline", "Liam",  "M"),
    (5, "Trickster_ChronicallyOnline",   "Trickster_ChronicallyOnline", "Liam",  "M"),
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
    for i in range(10):
        mapping.append((f"{prefix}_{bff_gender}_{i+1}.mp3", bff_lines[i][0], bff_lines[i][1]))
    for i in range(10, 19):
        mapping.append((f"{prefix}_{bff_gender}_{i+1}.mp3", bff_lines[i][0], bff_lines[i][1]))
    mapping.append((f"{prefix}_{bff_gender}_20_Y.mp3", bff_lines[19][0], bff_lines[19][1]))
    mapping.append((f"{prefix}_{bff_gender}_20_N.mp3", bff_lines[20][0], bff_lines[20][1]))
    for i in range(21, 26):
        mapping.append((f"{prefix}_{bff_gender}_{i}.mp3", bff_lines[i][0], bff_lines[i][1]))
    mapping.append((f"{prefix}_F_26_Y.mp3", bff_lines[26][0], True))
    mapping.append((f"{prefix}_{bff_gender}_26_N.mp3", bff_lines[27][0], False))
    mapping.append((f"{prefix}_{bff_gender}_27.mp3", bff_lines[28][0], False))
    mapping.append((f"{prefix}_{bff_gender}_28.mp3", bff_lines[29][0], False))
    mapping.append((f"{prefix}_F_29.mp3", bff_lines[30][0], True))
    mapping.append((f"{prefix}_F_30.mp3", bff_lines[31][0], True))
    mapping.append((f"{prefix}_F_31.mp3", bff_lines[32][0], True))
    mapping.append((f"{prefix}_{bff_gender}_32.mp3", bff_lines[33][0], False))
    for i in range(34, 41):
        mapping.append((f"{prefix}_{bff_gender}_{i-1}.mp3", bff_lines[i][0], False))
    mapping.append((f"{prefix}_{bff_gender}_40.mp3", bff_lines[41][0], False))
    for idx, line_idx in enumerate(range(42, 49)):
        mapping.append((f"{prefix}_{bff_gender}_{41+idx}_Y.mp3", bff_lines[line_idx][0], False))
    for idx, line_idx in enumerate(range(49, 57)):
        mapping.append((f"{prefix}_{bff_gender}_{43+idx}_N.mp3", bff_lines[line_idx][0], False))
    mapping.append((f"{prefix}_{bff_gender}_52.mp3", bff_lines[57][0], False))
    for idx, line_idx in enumerate(range(58, 61)):
        mapping.append((f"{prefix}_{bff_gender}_{53+idx}.mp3", bff_lines[line_idx][0], False))
    mapping.append((f"{prefix}_{bff_gender}_56.mp3", bff_lines[61][0], False))
    mapping.append((f"{prefix}_{bff_gender}_56_Y.mp3", bff_lines[62][0], False))
    mapping.append((f"{prefix}_{bff_gender}_57_Y.mp3", bff_lines[63][0], False))
    mapping.append((f"{prefix}_{bff_gender}_57_N.mp3", bff_lines[64][0], False))
    mapping.append((f"{prefix}_{bff_gender}_58_N.mp3", bff_lines[65][0], False))
    mapping.append((f"{prefix}_{bff_gender}_59_N.mp3", bff_lines[66][0], False))
    mapping.append((f"{prefix}_{bff_gender}_60.mp3", bff_lines[67][0], False))
    mapping.append((f"{prefix}_{bff_gender}_61.mp3", bff_lines[68][0], False))
    mapping.append((f"{prefix}_{bff_gender}_62.mp3", bff_lines[69][0], False))
    mapping.append((f"{prefix}_{bff_gender}_63.mp3", bff_lines[70][0], False))
    return mapping

def extract_word_timestamps(alignment):
    chars = alignment.get("characters", [])
    starts = alignment.get("character_start_times_seconds", [])
    ends = alignment.get("character_end_times_seconds", [])
    words = []
    current_word = []
    word_start = None
    for i, c in enumerate(chars):
        if c.isspace():
            if current_word:
                w_str = "".join(current_word)
                w_end = ends[i-1] if i > 0 else starts[i]
                words.append({"word": w_str, "start": round(word_start, 3), "end": round(w_end, 3)})
                current_word = []
                word_start = None
        else:
            if word_start is None:
                word_start = starts[i]
            current_word.append(c)
    if current_word:
        w_str = "".join(current_word)
        w_end = ends[-1] if ends else starts[-1]
        words.append({"word": w_str, "start": round(word_start, 3), "end": round(w_end, 3)})
    total_dur = max(ends) if ends else 0.0
    return words, round(total_dur, 3)

def generate_line(text, voice_cfg, out_mp3_path, out_json_path):
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
                
                # Save matching updated timestamp file as well
                alignment = data.get("alignment")
                if alignment:
                    words, dur = extract_word_timestamps(alignment)
                    meta = {
                        "text": clean,
                        "duration": dur,
                        "timestamps": words
                    }
                    with open(out_json_path, "w") as f:
                        json.dump(meta, f, indent=2, ensure_ascii=False)
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
    print("AI BFF REGENERATOR — FIXING 3 FLAT VERSIONS WITH eleven_v4")
    print(f"Model: {MODEL} | Output: {AUDIO_DIR}")
    print("=" * 70)
    
    for v_num, folder_name, prefix, voice_key, bff_gender in TARGET_VERSIONS:
        folder_path = os.path.join(AUDIO_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        bff_voice = VOICE_PROFILES[voice_key]
        riley_voice = VOICE_PROFILES["Riley_Crush"]
        overrides = OVERRIDE_LINES.get(folder_name, {})
        
        section_text = sections[v_num]
        bff_lines = parse_section_lines(section_text)
        mapping = build_file_mapping(prefix, bff_gender, bff_lines)
        
        print(f"\n[REGENERATING] {folder_name} (Voice: {voice_key}, Model: {MODEL}, Lines: {len(mapping)})")
        
        for idx, (filename, raw_text, is_crush) in enumerate(mapping, 1):
            text_to_use = overrides.get(filename, raw_text)
            out_mp3 = os.path.join(folder_path, filename)
            out_json = os.path.join(folder_path, filename.replace(".mp3", ".json"))
            
            voice_cfg = riley_voice if is_crush else bff_voice
            voice_name = "Riley" if is_crush else voice_key
            
            clean_display = strip_emojis(text_to_use)[:45]
            print(f"  [{idx:02d}/{len(mapping)}] {filename} ({voice_name}): {clean_display}...")
            
            success = generate_line(text_to_use, voice_cfg, out_mp3, out_json)
            if not success:
                print(f"    FAILED: {filename}")
            
            time.sleep(0.3)  # Brief pause between requests

    print("\n" + "=" * 70)
    print("REGENERATION COMPLETE FOR ALL 3 VERSIONS!")
    print("=" * 70)

if __name__ == "__main__":
    main()
