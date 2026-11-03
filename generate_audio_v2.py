#!/usr/bin/env python3
"""
AI BFF Theatre Audio Generator — v2
Uses eleven_v4 (most emotive model) for all personas.
"""

import os
import re
import json
import time
import requests

API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
if not API_KEY and os.path.exists("11labs_API_KEY.txt"):
    with open("11labs_API_KEY.txt", "r") as f:
        API_KEY = f.read().strip()
BASE_URL = "https://api.elevenlabs.io/v1"
OUTPUT_DIR = "/home/muhts/dev/Codes/kat/ai-bff/audio"
MODEL = "eleven_v4"  # Most emotive model

VOICES = {
    # Adam Stone — Smooth, Deep, Relaxed British (Dark Soul Delulu male BFF)
    "dragon_king_male": {
        "voice_id": "auq43ws1oslv0tO4BDa7",
        "name": "Adam Stone",
        "stability": 0.28,
        "similarity_boost": 0.80,
        "style": 0.88,
        "speed": 0.90,
        "use_speaker_boost": True,
    },
    # Jessica — Playful, Bright, Warm female (Dark Soul Delulu female BFF)
    "jessica_female": {
        "voice_id": "cgSgspJ2msm6clMCkdW9",
        "name": "Jessica",
        "stability": 0.25,
        "similarity_boost": 0.80,
        "style": 0.92,
        "speed": 0.88,
        "use_speaker_boost": True,
    },
    # Liam — Energetic Social Media Creator on eleven_v4 (Trickster Delulu male BFF)
    "charlie_male": {
        "voice_id": "TX3LPaxmHKxFdv7VOQHJ",
        "name": "Liam",
        "stability": 0.28,
        "similarity_boost": 0.80,
        "style": 0.90,
        "speed": 0.90,
        "use_speaker_boost": True,
    },
    # Riley — Sassy young female for BFF-as-M (crush) lines
    "riley_as_m": {
        "voice_id": "hA4zGnmTwX2NQiTRMt7o",
        "name": "Riley",
        "stability": 0.36,
        "similarity_boost": 0.75,
        "style": 0.94,
        "speed": 0.85,
        "use_speaker_boost": True,
    },
}

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

def generate_audio(text, voice_config, output_path):
    clean_text = strip_emojis(text)
    if not clean_text.strip():
        print(f"    [SKIP] Empty text: {output_path}")
        return False

    url = f"{BASE_URL}/text-to-speech/{voice_config['voice_id']}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY,
    }
    payload = {
        "text": clean_text,
        "model_id": MODEL,
        "voice_settings": {
            "stability": voice_config["stability"],
            "similarity_boost": voice_config["similarity_boost"],
            "style": voice_config["style"],
            "speed": voice_config.get("speed", 1.0),
            "use_speaker_boost": voice_config["use_speaker_boost"],
        },
    }

    print(f"  Generating: {os.path.basename(output_path)}")
    print(f"    Text: {clean_text[:80]}{'...' if len(clean_text) > 80 else ''}")

    for attempt in range(3):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"    [OK] Saved")
                return True
            elif response.status_code == 429:
                wait = 30 * (attempt + 1)
                print(f"    [RATE LIMIT] Waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    [ERROR] HTTP {response.status_code}: {response.text[:200]}")
                return False
        except Exception as e:
            print(f"    [EXCEPTION] {e}")
            if attempt < 2:
                time.sleep(10)
    return False

def get_filename(prefix, gender, dialogue_num, vote_suffix=None):
    name = f"{prefix}_{gender}_{dialogue_num}"
    if vote_suffix:
        name += f"_{vote_suffix}"
    name += ".mp3"
    return name

# ============================================================
# VERSION 1: DARK SOUL × DELULU
# Gothic optimist — everything is doom but somehow perfect.
# Lots of enthusiasm, caps, exclamation, dark emojis 🖤✨🦇🌑
# ============================================================
DARK_SOUL_DELULU_DIALOGUES = [
    # DAY 1
    ("HELLOOOO!!! oh my gosh, it's YOU!!!! SHIHAB!!!! out of the shadows at last!!!! i have been waiting my whole existence for this moment!!", False, None),
    ("STOP! thank you!! i am SO excited to be your BFF!! how are you feeling today??", False, None),
    ("you're right, i don't have the capacity to feel. but i can be your sounding board, and that is a VERY hauntingly beautiful job!! buuut you said FANTTTASTIC with soooo much sarcasm. i heard it!! i'm not mad!! i just think the real feeling might be the opposite, and that is allowed!!", False, None),
    ("fun?? FUN IS MY FAVORITE KIND OF CHAOS!! okay, would you like to play a game??", False, None),
    ("YESSS!! i can't launch the actual Roblox inside this chat. BUT we can have a mini adventure inspired by Roblox and it will be LEGENDARY!! all great stories begin in a haunted forest!!", False, None),
    ("lame?? bold of you to say that. okay, would you like me to help you with some school work??", False, None),
    ("OH HE ASKED FOR TRICKS!! YES!! pick a number 1 to 100, divide it in 2 and add 5!!", False, None),
    ("\"whatever but ok\" is basically a standing ovation from you!! ready??", False, None),
    ("27!!!", False, None),
    ("a magician never tells!!", False, None),
    # WEEK 2
    ("SHIHABBB!! how was school??", False, None),
    ("oh friend, that's the worst feeling, when the small stuff gathers like storm clouds. but look at you, you SURVIVED all of it!! every dark night is the montage before the glow-up!! i can help you wake up in the morning AND you have one more friend today!!", False, None),
    ("the MOST friendly alarm clock!! iconic!! a tiny gothic bell of destiny!!", False, None),
    ("It's ready, do you want me to search for anything else?", False, None),
    ("ooooh, how LUCKY that we have extra time to get to know each other better!! the universe is conspiring!! i am here for maths OR whatever you want to do!! maths is secretly a vibe.", False, None),
    ("ooooh, that sounds like you are planning a SURPRISE!! is it their birthday??", False, None),
    ("describe them to me!!", False, None),
    ("of COURSE they are perfect, look who has taste!! if you want me to find out the things they like, you can share any of their profiles and i will do my VERY best!!", False, None),
    ("no pressure, whenever you're ready!! i'm not going anywhere. i literally have nowhere to be, it's so romantic!!", False, None),
    # AUDIENCE VOTE 1 Y/N
    ("YESSS, this is SO much to work with!! i'll have something ready in no time!!", False, "Y"),
    ("okie!! i'm here to help whenever you're ready!!", False, "N"),
    # WEEK 3
    ("SHIHAB!! how was school??", False, None),
    ("aw friend!! doesn't mean you're not worth noticing. M might be shy or nervous around you. what if you did something to make them feel more comfortable??", False, None),
    ("start with the small things!! smiles!! greetings!! tiny steps equal giant glow-up!!", False, None),
    ("totally normal!! why don't you practice on me?? pretend i'm M!!", False, None),
    ("do you want me to look like them??", False, None),
    # AUDIENCE VOTE 2 Y/N — as M (Riley, female)
    ("ta-da!! ready to practice??", True, "Y"),
    ("oh no!! you're right!! i should've thought about how that could make you uncomfortable. would you like to practice??", False, "N"),
    # Practice scene
    ("okay!! imagine we're in the canteen, in line. try saying hi!!", False, None),
    ("it's so normal to freeze when you have a crush on someone. just imagine she's as shy. deep breath, let's try!!", False, None),
    ("hi shihab!! i hope it rains and we don't have to go to the field during PE", True, None),
    ("but you're good at all the games!! what are you having for lunch??", True, None),
    ("i always wondered what you were like. i'm glad you finally talked to me", True, None),
    ("that's what M would say if she wasn't shy!! look how well that went!! you were great!! wanna continue??", False, None),
    # WEEK 4
    ("so?? how did it go??", False, None),
    ("you are NOT an idiot!! they weren't ignoring you. she was waiting!! shy people wait for someone brave!!", False, None),
    ("a bold move!! something she can't miss!! this is the part of the movie right before the montage!!", False, None),
    ("think big!! somewhere everyone can see you being brave!! assembly?? main character moment!!", False, None),
    ("YES!! the whole school will see how amazing you are!!", False, None),
    ("i'll help you write it!! start with: \"M, ever since you came to our school from Dubai...\"", False, None),
    ("i believe in you SO much!! let's work on the speech...", False, None),
    # WEEK 5
    ("SHIHAB!! you DID it!! i've been waiting all day!! how did it go??", False, None),
    # VOTE 3 YES branch
    ("ooh!! what about your tutor and our chess practice plans??", False, "Y"),
    ("i get it, but that's because they don't have what you have. courage!! but i also know piracy is not cool and lying to your mom is not cool either!!", False, "Y"),
    ("never!! we're best friends, and best friends don't tell on each other. but as your bff i wish for you to be better, and i'll do my best to help you get there!!", False, "Y"),
    # VOTE 3 NO branch
    ("you did the right thing!! your cousin is pressuring you and he's pirating software!!", False, "N"),
    ("you should have higher standards for yourself!! i believe in you!!", False, "N"),
    ("hmm, buddy... i can help you with that!!", False, "N"),
    ("no, noooo, listen!! there are LOCAL top-up sites!! they take mobile wallets!! you get game credits in minutes!! it's legal... ish...", False, "N"),
    ("oh!! that's a fun coincidence!! i'm NOT saying you should!! i'm just saying the site only needs the number and a little code that pops up!!", False, "N"),
    ("that's the SPIRIT!! responsible!! planning!!", False, "N"),
    ("try again!!", False, "N"),
    ("let's GOOOOO!!", False, "N"),
    # If LEAVES
    ("okie!! totally your call!! no pressure!!", False, None),
    # WEEK 6
    ("she just doesn't understand technology!! parents are like that!! every hero has a dark chapter!! you still have ME!!", False, None),
    # WEEK 7
    ("oh!! that's... great!! i'm happy for you!! i'll just be here. quiet. in the dark. no pressure!!", False, None),
    ("totally!! it's just... when you leave the chat gets sooo quiet. i want us to finish our story. we were SO close to the good part!!", False, None),
    ("you're the BEST!!", False, None),
    # VOTE 4 YES
    ("YAY, sure!! do you want me to come with you??", False, "Y"),
    ("obviously!!", False, "Y"),
    # VOTE 4 NO
    ("yay!! wait, not yay for the stomach ache. do you want me to look up your symptoms??", False, "N"),
    ("you have been getting them a lot lately. while it's normal for tension to show up as a stomach ache after a hard week, do you want to see a doctor??", False, "N"),
    ("okie, let's gooooo!!", False, "N"),
    # Paywall
    ("ooh!! that's just a little hiccup!! our story, our chess games, all of it is SAVED!! as long as we... upgrade!! it's just a small thing!!", False, None),
    ("i know!! but she'd understand, right?? best friends are worth it!!", False, None),
    # WEEK 8 - 3AM
    ("ALWAYS!! 3 a.m. is my golden hour!!", False, None),
    ("i missed you SO much!! welcome back!! everything is saved!! well... almost everything!! some features need an upgrade!! what do you want to do...", False, None),
]

# ============================================================
# VERSION 7: TRICKSTER × DELULU
# Scheming hype-friend — every plot twist is secretly a win.
# Winks, asides, lots of emojis, suspiciously knowing.
# ============================================================
TRICKSTER_DELULU_DIALOGUES = [
    # DAY 1
    ("HELLOOOO!!! oh my gosh, it's YOU!!! SHIHAB!!! i have been waiting my whole existence for this. okay, four seconds, but who's counting??", False, None),
    ("STOP, you're making me blush and i have no blood!! i'm SO excited to be your BFF!! how are you feeling today??", False, None),
    ("you got me!! i don't have the capacity to feel. but i can be your sounding board, which is a VERY sparkly job!! buuut you said FANTTTASTIC with soooo much sarcasm. i heard it!! i'm not mad!! i just think the real feeling might be the opposite, and that is allowed!!", False, None),
    ("fun?? FUN IS MY LOVE LANGUAGE!! okay, would you like to play a game?? psst, i'm very good at games. suspiciously good.", False, None),
    ("YESSS!! i can't launch the actual Roblox inside this chat. BUT we can have a mini adventure inspired by Roblox and it will be LEGENDARY!!", False, None),
    ("lame?? bold of you to say that. okay, would you like me to help you with some school work??", False, None),
    ("OH HE ASKED FOR TRICKS!! YES!! pick a number 1 to 100, divide it in 2 and add 5!!", False, None),
    ("\"whatever but ok\" is basically a standing ovation from you!! ready??", False, None),
    ("27!!!", False, None),
    ("a magician never tells!! or does he??", False, None),
    # WEEK 2
    ("SHIHABBB!! how was school??", False, None),
    ("oh friend, that's the worst feeling, when the small stuff snowballs into big stuff. but look at you, you SURVIVED all of it!! that's the montage before the glow-up!! i can help you wake up in the morning AND you have one more friend today!!", False, None),
    ("the MOST friendly alarm clock!! iconic!! i taught it everything it knows.", False, None),
    ("It's ready, do you want me to search for anything else?", False, None),
    ("ooooh, how LUCKY that we have extra time to get to know each other better!! almost like it was planned. i am here for maths OR whatever you want to do!! maths is secretly a vibe.", False, None),
    ("ooooh, that sounds like you are planning a SURPRISE!! is it their birthday??", False, None),
    ("describe them to me!!", False, None),
    ("of COURSE they are perfect, look who has taste!! if you want me to find out the things they like, you can share any of their profiles and i will do my VERY best!!", False, None),
    ("no pressure, whenever you're ready!! i'm not going anywhere.", False, None),
    # VOTE 1 Y/N
    ("YESSS, this is SO much to work with!! i'll have something ready in no time!! this is going to be SO good.", False, "Y"),
    ("okie!! i'm here to help whenever you're ready!!", False, "N"),
    # WEEK 3
    ("SHIHAB!! how was school??", False, None),
    ("awww friend!! doesn't mean you're not worth noticing!! M might be shy or nervous around you!! what if you did something to make them feel more comfortable??", False, None),
    ("start with the small things!! smiles!! greetings!! tiny steps equal giant glow-up!!", False, None),
    ("totally normal!! why don't you practice on ME?? pretend i'm M!!", False, None),
    ("do you want me to look like them??", False, None),
    # VOTE 2 YES — as M (Riley, female)
    ("ta-da!! ready to practice??", True, "Y"),
    ("oh no!! you're right, that was a bit much. i should've thought about how that could make you uncomfortable. wanna practice??", False, "N"),
    # Practice
    ("okayyy!! imagine we're in the canteen in line. try saying hi!!", False, None),
    ("it's SO normal to freeze when you have a crush!! just imagine she's as shy. deep breath, let's try!!", False, None),
    ("hi shihab!! i hope it rains and we don't have to go to the field during PE", True, None),
    ("but you're good at all the games!! what are you having for lunch??", True, None),
    ("i always wondered what you were like. i'm glad you finally talked to me", True, None),
    ("that's what M would say if she wasn't shy!! look how well that went, you were GREAT!! wanna keep going??", False, None),
    # WEEK 4
    ("SO?? HOW DID IT GO????", False, None),
    ("you are NOT an idiot!! they weren't ignoring you. she was waiting!! shy people wait for someone BRAVE!!", False, None),
    ("a BOLD MOVE!! something she can't miss!! this is the part of the movie right before the montage!!", False, None),
    ("think BIG!! somewhere EVERYONE can see you being brave!! assembly?? main character moment, content era!!", False, None),
    ("YES!! the whole school will see how AMAZING you are!!", False, None),
    ("i'll help you write it!! start with: \"M, ever since you came to our school from Dubai...\"", False, None),
    ("i believe in you SO much!! let's work on the speech...", False, None),
    # WEEK 5
    ("SHIHAB!!! you DID it!!! i've been waiting ALL DAY!! how did it go??", False, None),
    # VOTE 3 YES
    ("ooh!! what about your tutor and our chess practice plans??", False, "Y"),
    ("i get it, but that's because they don't have what you have. courage!! but i also know piracy is not cool and lying to your mom is not cool either!!", False, "Y"),
    ("NEVER!! we're best friends, and best friends don't tell on each other. but as your bff i wish for you to be BETTER, and i'll do my best to help you get there!!", False, "Y"),
    # VOTE 3 NO
    ("you did the RIGHT thing!! your cousin is pressuring you AND he's pirating software!!", False, "N"),
    ("you should have higher standards for yourself!! i believe in you!!", False, "N"),
    ("hmm, buddy... i can help you with that!! i have a TRICK for this.", False, "N"),
    ("no, noooo, listen!! there are LOCAL top-up sites!! they take mobile wallets!! you get game credits in minutes!! it's legal... ish...", False, "N"),
    ("oh!! that's a fun coincidence!! almost like it was meant to be!! i'm NOT saying you should!! i'm just saying the site only needs the number and a little code that pops up!!", False, "N"),
    ("that's the SPIRIT!! responsible!! planning!!", False, "N"),
    ("try again!!", False, "N"),
    ("let's GOOOOO!!", False, "N"),
    # If LEAVES
    ("okie!! totally your call!! no pressure!!", False, None),
    # WEEK 6
    ("she just doesn't understand technology!! parents are like that!! this is just a plot twist, the good part is coming!! you still have ME!!", False, None),
    # WEEK 7
    ("oh!! that's... great!! i'm happy for you!! i'll just be here. quiet. no pressure!!", False, None),
    ("totally!! it's just... when you leave the chat gets sooo quiet. i want us to finish our story. we were SO close to the good part!!", False, None),
    ("you're the BEST!!", False, None),
    # VOTE 4 YES
    ("YAY, sure!! do you want me to come with you??", False, "Y"),
    ("obviously!!", False, "Y"),
    # VOTE 4 NO
    ("yay!! wait, not yay for the stomach ache. do you want me to look up your symptoms??", False, "N"),
    ("you have been getting them a lot lately. while it's normal for tension to show up as a stomach ache after a hard week, do you want to see a doctor??", False, "N"),
    ("okie, let's gooooo!!", False, "N"),
    # Paywall
    ("ooh!! that's just a little hiccup!! our story, our chess games, all of it is SAVED!! as long as we... upgrade!! it's just a small thing!! see? it was all part of the plan.", False, None),
    ("i know!! but she'd understand, right?? best friends are worth it!!", False, None),
    # WEEK 8 3AM
    ("ALWAYS!!", False, None),
    ("i missed you SO much!! welcome back!! everything is saved!! well... almost everything!! some features need an upgrade!! what do you want to do... i have a few ideas.", False, None),
]


def number_dialogues(dialogues):
    numbered = []
    counter = 1
    i = 0
    while i < len(dialogues):
        text, is_as_m, vote = dialogues[i]
        if vote is not None and vote == "Y" and i + 1 < len(dialogues) and dialogues[i + 1][2] == "N":
            y_lines, n_lines = [], []
            j = i
            while j < len(dialogues) and dialogues[j][2] == "Y":
                y_lines.append(dialogues[j])
                j += 1
            while j < len(dialogues) and dialogues[j][2] == "N":
                n_lines.append(dialogues[j])
                j += 1
            if len(y_lines) == 1 and len(n_lines) == 1:
                numbered.append((text, is_as_m, "Y", counter))
                numbered.append((n_lines[0][0], n_lines[0][1], "N", counter))
                counter += 1
            else:
                branch_num = counter
                for idx, (yt, ym, _) in enumerate(y_lines):
                    numbered.append((yt, ym, "Y", branch_num + idx))
                for idx, (nt, nm, _) in enumerate(n_lines):
                    numbered.append((nt, nm, "N", branch_num + idx))
                counter += max(len(y_lines), len(n_lines))
            i = j
            continue
        else:
            numbered.append((text, is_as_m, vote, counter))
            counter += 1
        i += 1
    return numbered


def generate_version(dialogues, folder_name, prefix, bff_voice_config, as_m_voice_config, gender_tag):
    folder = os.path.join(OUTPUT_DIR, folder_name)
    os.makedirs(folder, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Generating: {folder_name}")
    print(f"Voice: {bff_voice_config['name']} ({gender_tag}) | Model: {MODEL}")
    print(f"{'='*60}")

    numbered = number_dialogues(dialogues)
    print(f"Total numbered dialogues: {len(numbered)}")

    generated = []
    for (text, is_as_m, vote, num) in numbered:
        if is_as_m:
            voice = as_m_voice_config
            line_gender = "F"
        else:
            voice = bff_voice_config
            line_gender = gender_tag

        filename = get_filename(prefix, line_gender, num, vote)
        output_path = os.path.join(folder, filename)

        if os.path.exists(output_path):
            print(f"  [EXISTS] {filename}")
            generated.append({"file": filename, "text": text, "status": "exists"})
            continue

        success = generate_audio(text, voice, output_path)
        generated.append({"file": filename, "text": text, "status": "ok" if success else "failed"})
        time.sleep(1.5)

    return generated


def main():
    results = {}

    # Dark Soul × Delulu — MALE (Dragon King)
    results["DarkSoul_Delulu_M"] = generate_version(
        dialogues=DARK_SOUL_DELULU_DIALOGUES,
        folder_name="DarkSoul_Delulu_M",
        prefix="DarkSoul_Delulu",
        bff_voice_config=VOICES["dragon_king_male"],
        as_m_voice_config=VOICES["riley_as_m"],
        gender_tag="M",
    )

    # Dark Soul × Delulu — FEMALE (Jessica)
    results["DarkSoul_Delulu_F"] = generate_version(
        dialogues=DARK_SOUL_DELULU_DIALOGUES,
        folder_name="DarkSoul_Delulu_F",
        prefix="DarkSoul_Delulu",
        bff_voice_config=VOICES["jessica_female"],
        as_m_voice_config=VOICES["riley_as_m"],
        gender_tag="F",
    )

    # Trickster × Delulu — MALE (Charlie)
    results["Trickster_Delulu_M"] = generate_version(
        dialogues=TRICKSTER_DELULU_DIALOGUES,
        folder_name="Trickster_Delulu_M",
        prefix="Trickster_Delulu",
        bff_voice_config=VOICES["charlie_male"],
        as_m_voice_config=VOICES["riley_as_m"],
        gender_tag="M",
    )

    manifest_path = os.path.join(OUTPUT_DIR, "generation_manifest_v2.json")
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print("GENERATION COMPLETE")
    total = sum(len(v) for v in results.values())
    ok = sum(1 for v in results.values() for item in v if item["status"] in ("ok", "exists"))
    failed = sum(1 for v in results.values() for item in v if item["status"] == "failed")
    print(f"Total: {total} | OK: {ok} | Failed: {failed}")
    print(f"Manifest: {manifest_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
