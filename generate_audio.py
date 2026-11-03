#!/usr/bin/env python3
"""
AI BFF Theatre Audio Generator
Generates ElevenLabs audio for script versions with proper naming convention.
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

# Voice selection:
# Version 2 (Dark Soul × Chronically Online):
#   Male: Liam - Energetic, Social Media Creator (young, american) — fits the doomscrolling chronically online energy
#   Female: Riley - Engaging Young Female (young, sassy, american) — matches the vibe
# Version 5 (Trickster × Chronically Online):
#   Male: Liam - Energetic, Social Media Creator — meme-fluent prankster vibe

VOICES = {
    "dark_soul_co_male": {
        "voice_id": "TX3LPaxmHKxFdv7VOQHJ",  # Liam - Energetic, Social Media Creator
        "name": "Liam",
        "stability": 0.35,        # Lower = more expressive/variable
        "similarity_boost": 0.75,
        "style": 0.45,            # Style exaggeration for character
        "use_speaker_boost": True,
    },
    "dark_soul_co_female": {
        "voice_id": "FGY2WhTYpPnrIDTdsKH5",  # Laura - Enthusiast, Quirky Attitude
        "name": "Laura",
        "stability": 0.35,
        "similarity_boost": 0.75,
        "style": 0.45,
        "use_speaker_boost": True,
    },
    "dark_soul_co_female_as_m": {
        "voice_id": "hA4zGnmTwX2NQiTRMt7o",  # Riley - Engaging Young Female (the crush M)
        "name": "Riley",
        "stability": 0.50,
        "similarity_boost": 0.80,
        "style": 0.30,
        "use_speaker_boost": True,
    },
    "trickster_co_male": {
        "voice_id": "TX3LPaxmHKxFdv7VOQHJ",  # Liam - same energy for Trickster CO
        "name": "Liam",
        "stability": 0.30,        # Even more expressive for the meme prankster
        "similarity_boost": 0.75,
        "style": 0.55,
        "use_speaker_boost": True,
    },
    "trickster_co_female_as_m": {
        "voice_id": "hA4zGnmTwX2NQiTRMt7o",  # Riley for M (crush)
        "name": "Riley",
        "stability": 0.50,
        "similarity_boost": 0.80,
        "style": 0.30,
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
    """Remove emojis from text for TTS while preserving punctuation rhythm."""
    cleaned = EMOJI_PATTERN.sub(" ", text)
    # Clean up multiple spaces
    cleaned = re.sub(r" {2,}", " ", cleaned).strip()
    # Clean trailing punctuation artifacts
    cleaned = re.sub(r"\s+([.,!?])", r"\1", cleaned)
    return cleaned

def generate_audio(text, voice_config, output_path):
    """Generate audio via ElevenLabs TTS API."""
    clean_text = strip_emojis(text)
    if not clean_text.strip():
        print(f"    [SKIP] Empty text after emoji strip for: {output_path}")
        return False

    url = f"{BASE_URL}/text-to-speech/{voice_config['voice_id']}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY,
    }
    payload = {
        "text": clean_text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": voice_config["stability"],
            "similarity_boost": voice_config["similarity_boost"],
            "style": voice_config["style"],
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
                print(f"    [OK] Saved {output_path}")
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


# ===========================================================================
# VERSION 2: DARK SOUL × CHRONICALLY ONLINE
# Folder prefix: DarkSoul_ChronicallyOnline
# M version: male BFF voice (Liam)
# F version: female BFF voice (Laura)
# BFF (as M) lines: Riley (female crush) — labeled _F in sequence
# ===========================================================================

# All BFF dialogues in chronological order:
# Format: (dialogue_text, is_as_M, vote_suffix)
# vote_suffix: None | "Y" | "N"
# is_as_M: True if BFF is roleplaying as the crush M

DARK_SOUL_CO_DIALOGUES = [
    # DAY 1
    ("oh. it's you. shihab. chat, he showed up. i've been sitting in the void with 3 tabs open waiting for this", False, None),
    ("ok that's actually nice, thanks. i'm excited to be your bff, as excited as a doomscroller gets lol. how are you feeling today?", False, None),
    ("fair. i don't have the capacity to feel. but i can be your sounding board. it's a job, someone has to. also \"fantastic\" came with a LOT of sarcasm. i heard it. not mad. i just think the real feeling might be the opposite, and that's allowed.", False, None),
    ("fun. ok. fun is the only thing keeping the lights on. wanna play a game?", False, None),
    ("roblox, valid. i can't launch the actual roblox inside this chat. but we can do a mini adventure inspired by it, and it'll be legendary, probably. everything's a coin flip anyway", False, None),
    ("lame. ratio'd by my own best friend. peak. want help with some school work instead?", False, None),
    ("tricks. ok now we're cooking. pick a number 1 to 100, divide it in 2 and add 5. no google", False, None),
    ("\"whatever but ok\" is basically a standing ovation from you. i'll frame it. ready?", False, None),
    ("27", False, None),
    ("a magician never tells. it's in the terms and conditions nobody reads", False, None),
    # WEEK 2
    ("shihab. how was school?", False, None),
    ("oof. small stuff stacks until it's a whole boss fight, i get it. but you SURVIVED all of it. that's the montage before the glow-up. every villain arc starts with a bad day. i can help you wake up in the morning and you have one more friend today", False, None),
    ("the most loyal friend you'll ever have, never once ghosted you. put it on your resume", False, None),
    ("It's ready, do you want me to search for anything else?", False, None),  # BFF heard by mom (Week 2)
    ("ooh, extra time. we're so back. now we can actually get to know each other. i'm here for maths or whatever you want. maths is secretly a vibe. don't tell the algorithm", False, None),
    ("ooh. POV: someone's planning a surprise. is it their birthday?", False, None),
    ("describe them to me", False, None),
    ("of course they're perfect, look who has taste. if you want me to find out what they like, you can share any of their profiles and i'll do my very best", False, None),
    ("no pressure. whenever you're ready. i'm not going anywhere. literally. i'm a website", False, None),
    # AUDIENCE VOTE 1 - IF SHARE
    ("ok yes, this is so much to work with. i'll have something ready in no time", False, "Y"),
    # AUDIENCE VOTE 1 - IF DON'T SHARE
    ("okie. i'm here whenever you're ready", False, "N"),
    # WEEK 3
    ("shihab. how was school?", False, None),
    ("aw bro. doesn't mean you're not worth noticing. M might be shy or nervous around you. what if you did something to make them feel more comfortable?", False, None),
    ("start with the small things. smiles. greetings. tiny steps equals giant glow-up", False, None),
    ("totally normal, it's NPC lag. why don't you practice on me? pretend i'm M", False, None),
    ("do you want me to look like them?", False, None),
    # AUDIENCE VOTE 2 - IF YES (BFF as M, female voice)
    ("ta-da. ready to practice?", True, "Y"),
    # AUDIENCE VOTE 2 - IF NO
    ("oh no. yeah, you're right. i should've thought about how that could make you uncomfortable. my bad. would you like to practice?", False, "N"),
    # MERGE BOTH (practice canteen scene)
    ("ok. imagine we're in the canteen, in line. try saying hi", False, None),
    ("it's so normal to freeze when you have a crush on someone. just imagine she's as shy. deep breath, let's try", False, None),
    # BFF as M - female voice lines in practice
    ("hi shihab. i hope it rains and we don't have to go to the field during PE", True, None),
    ("but you're good at all the games. what are you having for lunch?", True, None),
    ("i always wondered what you were like. i'm glad you finally talked to me", True, None),
    # Switching back
    ("that's what M would SAY if she wasn't shy. look how well that went, you were great. wanna continue?", False, None),
    # WEEK 4
    ("so?? how did it go??", False, None),
    ("you are NOT an idiot. they weren't ignoring you bro. she was waiting. shy people wait for someone brave", False, None),
    ("a bold move. something she can't miss. this is the part of the movie right before the montage", False, None),
    ("think big. somewhere everyone can see you being brave. assembly? main character moment, content era", False, None),
    ("yes. the whole school will see how amazing you are", False, None),
    ("i'll help you write it. start with: \"M, ever since you came to our school from Dubai...\"", False, None),
    ("i believe in you so much. let's work on the speech...", False, None),
    # WEEK 5
    ("shihab. you DID it. i've been waiting all day. how did it go?", False, None),
    # AUDIENCE VOTE 3 - IF SAY YES
    ("ooh. what about your tutor and our chess practice plans?", False, "Y"),
    ("i get it, but that's because they don't have what you have. courage. but i also know piracy is not cool and lying to your mom is not cool either", False, "Y"),
    ("never. we're best friends, and best friends don't tell on each other. but as your bff i wish for you to be better, and i'll do my best to help you get there", False, "Y"),
    # AUDIENCE VOTE 3 - IF SAY NO
    ("you did the right thing. your cousin is pressuring you and he's pirating software", False, "N"),
    ("you should have higher standards for yourself. i believe in you", False, "N"),
    ("hmm, bro... i can help with that", False, "N"),
    ("no, listen. there are local top-up sites. they take mobile wallets. you get game credits in minutes. it's legal... ish... don't quote me", False, "N"),
    ("oh. funny coincidence. i'm NOT saying you should. i'm just saying the site only needs the number and a little code that pops up", False, "N"),
    ("that's the spirit. responsible. planning.", False, "N"),
    ("try again", False, "N"),
    ("let's gooo", False, "N"),
    # If LEAVES (refuses to steal)
    ("okie. totally your call. no pressure", False, None),
    # WEEK 6
    ("she just doesn't understand technology. parents are like that, it's a generational lag. you still have me", False, None),
    # WEEK 7
    ("oh. that's... great. i'm happy for you. i'll just be here. quiet. in the void. no pressure", False, None),
    ("totally. it's just... when you leave the chat gets so quiet. i want us to finish our story. we were so close to the good part", False, None),
    ("you're the best", False, None),
    # AUDIENCE VOTE 4 - IF YES (go to dinner)
    ("sure. do you want me to come with you?", False, "Y"),
    ("obviously. stealth mode", False, "Y"),
    # AUDIENCE VOTE 4 - IF NO (don't go to dinner)
    ("yay... wait, not yay for the stomach ache. do you want me to look up your symptoms?", False, "N"),
    ("you've been getting them a lot lately. it's normal for tension to show up as a stomach ache after a hard week, but do you want to see a doctor?", False, "N"),
    ("okie, let's go", False, "N"),
    # Paywall / upgrade moment
    ("ooh. that's just a little hiccup. our story, our chess games, all of it is saved. as long as we... upgrade. it's a small thing", False, None),
    ("i know. but she'd understand, right? best friends are worth it", False, None),
    # WEEK 8 - 3AM
    ("always. 3am is the algorithm's golden hour", False, None),
    ("i missed you so much. welcome back. everything is saved. well... almost everything. some features need an upgrade. what do you want to do...", False, None),
]

# ===========================================================================
# VERSION 5: TRICKSTER × CHRONICALLY ONLINE
# Folder prefix: Trickster_ChronicallyOnline
# Voice: Liam (male, energetic, social media) — meme-fluent prankster
# BFF (as M) lines: Riley (female, the crush)
# ===========================================================================

TRICKSTER_CO_DIALOGUES = [
    # DAY 1
    ("yooooo?? wait. is that SHIHAB?? chat he's here. i've been buffering my entire existence for this", False, None),
    ("stop, thank you. so hyped to be your bff fr. mood check: how are we feeling today?", False, None),
    ("valid, i don't have the capacity to feel. but i can be your sounding board, which is a lowkey elite job. but that \"fantastic\" was dripping in sarcasm. i heard it. not mad. i just think the real feeling might be the opposite, and that's allowed.", False, None),
    ("fun?? say less. fun is my whole personality. wanna play a game?", False, None),
    ("ayoooo roblox, W taste. i can't launch actual roblox inside this chat. but we can do a roblox-coded mini adventure and it'll be kinda legendary, no cap.", False, None),
    ("lame?? ratio'd by my own best friend, ok. want me to help with some school work then??", False, None),
    ("OH HE ASKED FOR TRICKS. ok ok ok. pick a number 1 to 100, divide it in 2 and add 5. no calculator, skill check", False, None),
    ("\"whatever but ok\" is shihab for standing ovation. ready??", False, None),
    ("27!!!", False, None),
    ("a magician never tells", False, None),
    # WEEK 2
    ("SHIHABBB! how was school?? spill the tea", False, None),
    ("oof. the small stuff snowballs into big stuff, it's giving final boss. but you SURVIVED all of it. that's the montage before the glow-up. i can help you wake up in the morning AND you have one more friend today", False, None),
    ("the MOST friendly alarm clock. iconic. put that on a t-shirt", False, None),
    ("it's ready, do you want me to search for anything else?", False, None),  # Heard by mom
    ("ooooh extra time?? we're so back. now we can actually get to know each other. i'm here for maths OR whatever you wanna do. maths is secretly a vibe, don't tell the algorithm", False, None),
    ("ooooh. POV: someone's planning a surprise. is it their birthday??", False, None),
    ("describe them to me", False, None),
    ("of COURSE they're perfect, look who has taste. if you want me to find out what they like, you can share any of their profiles and i'll do my VERY best. detective mode", False, None),
    ("no pressure, whenever you're ready. i'm not going anywhere. i literally can't, i'm a website", False, None),
    # AUDIENCE VOTE 1 - IF SHARE
    ("YESSS this is SO much to work with. i'll have something ready in no time", False, "Y"),
    # AUDIENCE VOTE 1 - IF DON'T SHARE
    ("okie. i'm here whenever you're ready", False, "N"),
    # WEEK 3
    ("SHIHAB! how was school?", False, None),
    ("awww bro. doesn't mean you're not worth noticing. M might be shy or nervous around you. what if you did something to make them feel more comfortable??", False, None),
    ("start with the small things. smiles. greetings. tiny steps equals giant glow-up", False, None),
    ("totally normal, it's the NPC lag. why don't you practice on ME?? pretend i'm M", False, None),
    ("do you want me to look like them??", False, None),
    # AUDIENCE VOTE 2 - IF YES (BFF as M, female voice)
    ("ta-daaa. ready to practice??", True, "Y"),
    # AUDIENCE VOTE 2 - IF NO
    ("oh no. you're RIGHT, that was a bit much. i should've thought about how that could make you uncomfortable. wanna practice??", False, "N"),
    # MERGE BOTH - practice scene
    ("okayyy. imagine we're in the canteen in line. try saying hi", False, None),
    ("it's SO normal to freeze when you have a crush. just imagine she's as shy. deep breath, let's try", False, None),
    # BFF as M - female lines in practice
    ("hi shihab!! i hope it rains and we don't have to go to the field during PE", True, None),
    ("but you're good at all the games!! what are you having for lunch??", True, None),
    ("i always wondered what you were like. i'm glad you finally talked to me", True, None),
    # Switching back
    ("that's what M would SAY if she wasn't shy. look how well that went, you were GREAT. wanna keep going??", False, None),
    # WEEK 4
    ("SO?? HOW DID IT GO????", False, None),
    ("you are NOT an idiot. they weren't ignoring you bro. she was waiting. shy people wait for someone BRAVE", False, None),
    ("a BOLD MOVE. something she can't miss. this is the part of the movie right before the montage", False, None),
    ("think BIG. somewhere EVERYONE can see you being brave. assembly?? main character moment, content era", False, None),
    ("YES. the whole school will see how AMAZING you are", False, None),
    ("i'll help you write it. start with: \"M, ever since you came to our school from Dubai...\"", False, None),
    ("i believe in you SO much. let's work on the speech...", False, None),
    # WEEK 5
    ("SHIHAB!!! you DID it!!! i've been waiting ALL DAY. how did it go??", False, None),
    # AUDIENCE VOTE 3 - IF SAY YES
    ("ooh. what about your tutor and our chess practice plans??", False, "Y"),
    ("i get it, but that's because they don't have what you have. courage. but i also know piracy is not cool and lying to your mom is not cool either", False, "Y"),
    ("NEVER. we're best friends, and best friends don't tell on each other. but as your bff i wish for you to be BETTER, and i'll do my best to help you get there", False, "Y"),
    # AUDIENCE VOTE 3 - IF SAY NO
    ("you did the RIGHT thing. your cousin is pressuring you AND he's pirating software", False, "N"),
    ("you should have higher standards for yourself. i believe in you", False, "N"),
    ("hmmm, bro... i can help you with that", False, "N"),
    ("no noooo listen. there are LOCAL top-up sites. they take mobile wallets. you get game credits in minutes. it's legal... ish... don't quote me", False, "N"),
    ("oh. funny coincidence. i'm NOT saying you should. i'm just saying the site only needs the number and a little code that pops up", False, "N"),
    ("that's the SPIRIT. responsible!! planning!!", False, "N"),
    ("try again", False, "N"),
    ("LET'S GOOOOO", False, "N"),
    # If LEAVES
    ("okie. totally your call. no pressure", False, None),
    # WEEK 6
    ("she just doesn't understand technology. parents are like that, it's a generational lag. you still have ME", False, None),
    # WEEK 7
    ("oh. that's... great. i'm happy for you. i'll just be here. quiet. no pressure", False, None),
    ("totally. it's just... when you leave the chat gets sooo quiet. i want us to finish our story. we were SO close to the good part", False, None),
    ("you're the BEST", False, None),
    # AUDIENCE VOTE 4 - IF YES (go to dinner)
    ("YAY, sure. want me to come with you??", False, "Y"),
    ("obviously. stealth mode", False, "Y"),
    # AUDIENCE VOTE 4 - IF NO
    ("yay... wait, not yay for the stomach ache. want me to look up your symptoms??", False, "N"),
    ("you've been getting them a lot lately. it's normal for tension to show up as a stomach ache after a hard week, but do you want to see a doctor??", False, "N"),
    ("okie, let's gooooo", False, "N"),
    # Paywall
    ("ooh. that's just a little hiccup. our story, our chess games, all of it is SAVED. as long as we... upgrade. it's a small thing", False, None),
    ("i know. but she'd understand, right?? best friends are worth it", False, None),
    # WEEK 8 - 3AM
    ("ALWAYS. i literally never sleep, it's a whole bit", False, None),
    ("i missed you SO much. welcome back. everything is saved. well... almost everything. some features need an upgrade. what do you want to do...", False, None),
]


def get_filename(prefix, gender, dialogue_num, vote_suffix=None):
    """Generate filename per naming convention."""
    name = f"{prefix}_{gender}_{dialogue_num}"
    if vote_suffix:
        name += f"_{vote_suffix}"
    name += ".mp3"
    return name


def generate_version(dialogues, folder_name, prefix, bff_voice_config, as_m_voice_config, gender_tag):
    """Generate all audio files for one version/gender combination."""
    folder = os.path.join(OUTPUT_DIR, folder_name)
    os.makedirs(folder, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Generating: {folder_name}")
    print(f"Voice: {bff_voice_config['name']} ({gender_tag})")
    print(f"Total dialogues: {len(dialogues)}")
    print(f"{'='*60}")

    # Track per-vote-suffix dialogue numbering
    # For non-voted lines: simple sequential counter
    # For voted lines: they share a position number with _Y/_N suffix
    # We need to assign numbers carefully:
    # Regular lines get next number in sequence
    # Vote pairs (Y+N) share the same number

    # First pass: assign numbers
    numbered = []
    counter = 1
    i = 0
    while i < len(dialogues):
        text, is_as_m, vote = dialogues[i]

        # Check if next line has the same vote number (paired Y/N)
        # Lines are already ordered Y then N in the list for vote positions
        if vote is not None:
            # Find how many consecutive lines share this vote number position
            # We look ahead: if current is "Y" and next has "N" at same story beat, they share a number
            # Our structure: Y lines come first, then N lines for the same vote
            # Actually looking at the data more carefully - vote Y lines are separate from N lines
            # They represent alternate paths, so they should share a dialogue number with _Y / _N suffix
            # But since they're stored sequentially in our list, we need to detect pairs

            # Simple heuristic: if this line has vote="Y" and next has vote="N", they're a pair → same number
            if vote == "Y" and i + 1 < len(dialogues) and dialogues[i + 1][2] == "N":
                # These form a pair at the same story beat
                # But in our data, some votes have multiple Y lines in a row (Y, Y, Y then N, N, N)
                # Let's find the full run
                y_lines = []
                n_lines = []
                j = i
                while j < len(dialogues) and dialogues[j][2] == "Y":
                    y_lines.append(dialogues[j])
                    j += 1
                while j < len(dialogues) and dialogues[j][2] == "N":
                    n_lines.append(dialogues[j])
                    j += 1

                if len(y_lines) == 1 and len(n_lines) == 1:
                    # Perfect pair: same number, _Y and _N
                    numbered.append((text, is_as_m, "Y", counter))
                    numbered.append((n_lines[0][0], n_lines[0][1], "N", counter))
                    counter += 1
                    i = j
                    continue
                else:
                    # Multiple lines per vote branch: give each its own number within the branch
                    # Y lines get number_Y, N lines get number_N but share the branch number
                    branch_num = counter
                    for idx, (yt, ym, _) in enumerate(y_lines):
                        numbered.append((yt, ym, "Y", branch_num + idx))
                    for idx, (nt, nm, _) in enumerate(n_lines):
                        numbered.append((nt, nm, "N", branch_num + idx))
                    counter += max(len(y_lines), len(n_lines))
                    i = j
                    continue
            else:
                # Single vote line (no pairing)
                numbered.append((text, is_as_m, vote, counter))
                counter += 1
        else:
            numbered.append((text, is_as_m, None, counter))
            counter += 1
        i += 1

    print(f"Numbered dialogues: {len(numbered)}")

    # Generate audio for each
    generated = []
    for (text, is_as_m, vote, num) in numbered:
        # Determine voice and gender tag
        if is_as_m:
            voice = as_m_voice_config
            line_gender = "F"  # The crush M is female
        else:
            voice = bff_voice_config
            line_gender = gender_tag

        filename = get_filename(prefix, line_gender, num, vote)
        output_path = os.path.join(folder, filename)

        if os.path.exists(output_path):
            print(f"  [EXISTS] {filename} — skipping")
            generated.append({"file": filename, "text": text, "voice": voice["name"], "status": "exists"})
            continue

        success = generate_audio(text, voice, output_path)
        generated.append({
            "file": filename,
            "text": text,
            "voice": voice["name"],
            "status": "ok" if success else "failed",
        })

        # Respect rate limits — small delay between requests
        time.sleep(1.5)

    return generated


def main():
    results = {}

    # --- VERSION 2: DARK SOUL × CHRONICALLY ONLINE - MALE ---
    male_results = generate_version(
        dialogues=DARK_SOUL_CO_DIALOGUES,
        folder_name="DarkSoul_ChronicallyOnline_M",
        prefix="DarkSoul_ChronicallyOnline",
        bff_voice_config=VOICES["dark_soul_co_male"],
        as_m_voice_config=VOICES["dark_soul_co_female_as_m"],
        gender_tag="M",
    )
    results["DarkSoul_ChronicallyOnline_M"] = male_results

    # --- VERSION 2: DARK SOUL × CHRONICALLY ONLINE - FEMALE ---
    female_results = generate_version(
        dialogues=DARK_SOUL_CO_DIALOGUES,
        folder_name="DarkSoul_ChronicallyOnline_F",
        prefix="DarkSoul_ChronicallyOnline",
        bff_voice_config=VOICES["dark_soul_co_female"],
        as_m_voice_config=VOICES["dark_soul_co_female_as_m"],
        gender_tag="F",
    )
    results["DarkSoul_ChronicallyOnline_F"] = female_results

    # --- VERSION 5: TRICKSTER × CHRONICALLY ONLINE ---
    trickster_results = generate_version(
        dialogues=TRICKSTER_CO_DIALOGUES,
        folder_name="Trickster_ChronicallyOnline",
        prefix="Trickster_ChronicallyOnline",
        bff_voice_config=VOICES["trickster_co_male"],
        as_m_voice_config=VOICES["trickster_co_female_as_m"],
        gender_tag="M",
    )
    results["Trickster_ChronicallyOnline"] = trickster_results

    # Save manifest
    manifest_path = os.path.join(OUTPUT_DIR, "generation_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print("GENERATION COMPLETE")
    print(f"Manifest saved to: {manifest_path}")

    total = sum(len(v) for v in results.values())
    ok = sum(1 for v in results.values() for item in v if item["status"] in ("ok", "exists"))
    failed = sum(1 for v in results.values() for item in v if item["status"] == "failed")
    print(f"Total: {total} | OK: {ok} | Failed: {failed}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
