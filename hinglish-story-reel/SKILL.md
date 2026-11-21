---
name: hinglish-story-reel
description: Make a ~70 s Hindi/Hinglish Instagram Reel that tells a funny true story from the past (cons, scams, jail escapes, fake police stations, weird history), in the "Natwarlal sold the Taj Mahal" format, fully in code and free. Flat 2D cartoon people in a cel-shaded 3D world (Tall Tale 3D), a smooth Hindi AI narrator (Chatterbox multilingual), romanized Hinglish captions one or two words at a time, stickers and stamps, bounce music and sound effects, rendered to a 1080x1920 MP4. Use when someone wants a desi story reel, a Hindi or Hinglish storytime reel or short, a Natwarlal-type reel, a "kahani" reel about a real con man, scam, escape or strange event, or a true-story cartoon reel with a Hindi voiceover, even from just a topic.
---

# Hinglish Story Reel

You turn a true story into a finished vertical reel: research, a Hindi script with romanized captions, an AI Hindi voice,
word-synced captions, cartoon 3D shots, sound and music, MP4. Everything runs on the user's computer; no AI images or video,
no API keys, no credits. `SKILL` = the folder this file is in.

**What makes this format work** (it is the user-approved template from the Natwarlal reel):
- A shocking hook in the first line ("Ek aadmi tha, jisne Taj Mahal bech diya. Woh bhi ek baar nahi, kai baar!").
- A roast-style desi storyteller: cheeky, fast, "bhai", "socho", "ab asli twist suno". **Clean humour, no gaali.**
- About 13 lines, 60-75 s. Every line is one picture; the picture changes on the line.
- Numbers on screen as big stickers, red stamps on the punch ("SOLD", "GAAYAB!", "PAKDA GAYA"), postcards, progress bars.
- A twist ending, then the CTA: send it to a friend ("ye reel us dost ko bhejo jo...") and "LIKE KARO".

Built on the **faceless-shorts** skill's Tall Tale 3D engine (cartoon cut-out people, sets, camera, capture, mix). This skill
adds the Hindi voice pipeline, the romanized caption layer, extra sounds, the approved narrator reference and the story rules.

## 0. First use on a computer
1. The faceless-shorts skill must be installed (it has the engine) and its `scripts/setup.sh` must have run once.
2. `python SKILL/scripts/setup.py` until it prints **All set**. It builds `~/.hinglish-story-reel/venv` (PyTorch + Chatterbox +
   faster-whisper, several GB) and writes `~/.hinglish-story-reel/config.json`. If a venv with Chatterbox already exists
   (e.g. from the own-voice-dub skill) reuse it: `python SKILL/scripts/setup.py --use-python <venv python> --hf-home <its hf-cache>`.
   A GPU (CUDA) is strongly recommended; on CPU each take is slow.

## 1. Pick the story (wait for the user)
If the user gave a topic, use it. If they say "next", "more stories" or give none: offer 5-8 ideas, one line each (who, what,
why it's funny or shocking), and **let them pick. Never pick one yourself and start building.** Good ideas: desi cons and
jugaad (fake toll plaza, fake SBI branch, fake embassy, fake police station), jail escapes, Victor Lustig selling the Eiffel
Tower, the Captain of Köpenick, the Great Emu War, the Dancing Plague, Frank Abagnale, the Hitler Diaries hoax.
World stories are fine: told by the same desi narrator, with desi comparisons.

Once they've picked: **one flow.** Research, script, voice, build, QA and render without stopping for check-ins, then deliver.

## 2. Research
Check every fact against reliable sources (major outlets, encyclopaedias, museums, court records) and list them in
`script.json` "sources" with what each one supports. If sources disagree on a number, use the one most give. For legends
that can't be proven, the narrator says "कहते हैं" ("they say"). Private people who might be victims: don't name them.

## 3. Script (`script.json`)
Read `SKILL/references/script-rules.md` and `SKILL/example/script.json` (an approved reel) first.
```json
{ "title": "Bihar ka Nakli Thana", "captions": "roman", "lead": 0.3, "outro": 1.2, "gap": 0.18, "music": "bounce",
  "sources": ["..."],
  "lines": [ { "text": "<Devanagari Hindi, spoken>", "roman": "<the same line in Hinglish, English letters>",
               "say": "<optional: spelling the voice should read, if different>" } ] }
```
- `text` is Devanagari (Chatterbox needs it). `roman` is what appears on screen. Keep them word for word in the same
  order; captions map roman words onto the spoken word times by position.
- Numbers: in `text` write them as words ("पाँच सौ", "एक सौ पचास"); in `roman` use digits ("500", "150").
- Tragedies (deaths): respectful tone, `"music": "bed"`, no jokes about victims, no cartoon victims, a dark memorial card.

## 4. Build
1. `python SKILL/scripts/new_reel.py <short-name> --dir <parent>` (default: current folder) makes the project: engine,
   Hindi kit, the approved narrator reference `data/ref_voice.wav`, and the example `script.json` + `src/shots.js`.
2. Write `script.json`.
3. Voice: `python SKILL/scripts/voice.py <proj>` (run it **in the background** and wait; ~1-2 min per line on a GPU).
   It makes 3 takes per line, keeps the one Whisper hears best (no hint, so errors show), assembles, times every word,
   speeds up x1.12 with ffmpeg atempo, and prints a report. **Read the "heard" text of every line**, especially numbers
   (Chatterbox reads "तेईस" as 30, "डेढ़ सौ" as 200). Fix the wording (or add a `say`) and retake just those lines:
   `python SKILL/scripts/voice.py <proj> 4,9`. Lines flagged `s/word` may have a garbage tail: listen and retake.
4. Shots: read the faceless-shorts `styles/tall-tale/STYLE.md` (engine manual: `Toon`, sets, `shoot`, props), then
   rewrite `src/shots.js`, one shot per line (two for long lines). Start from the example's helpers: `LOOK` per character,
   `person()`, `sticker()`, stamps, the like CTA. Place cuts with `L(i)` and beats on words with `Wd('word', line)`
   (Devanagari words from `text`). Sounds: `cue(t, 'pop')` etc. (`pop plop boing stamp ding whoosh slide chirp chug thud
   slam tock alarm rev sputter levelup` ...). Stickers and stamps use Latin Hinglish text in Inter, never Devanagari.
5. In the project (Python = the `VPY` from config.json):
   `node tools/capture.mjs check` (must say CHECK OK) → `node tools/capture.mjs cues` → `VPY tools/mix.py .` →
   QA (section 5) → `node tools/capture.mjs video renders/<name>.mp4`. One shot: `node tools/capture.mjs frames review/f "4.2,4.6"`.

## 5. QA: never ship a frame you haven't looked at
`node tools/capture.mjs sheet review/all.jpg 0.5 10` and read the whole contact sheet, then key frames full size:
- The picture matches what the narrator is saying at that moment; reveals land on their word.
- Captions are romanized Hinglish, 1-2 words, no punctuation, spelled the way people type on Instagram, readable on a phone.
- Nothing crosses the caption zone (y 1250-1550) by accident; stickers don't cover faces.
- People face the camera (no slivers), stand on the floor, and look the same in every shot.
- Sound: voice clear over the music, effects soft. Fix, re-render the sheet, re-check. Tell the user what you caught.

## 6. Deliver
Open the MP4 for the user. Also give: a cover frame, an Instagram caption in Hinglish (hook + 1 line + a question to drive
comments), and 8-12 hashtags. Offer one round of changes and re-render only what changed.

## Never
Use gaali or slurs; invent facts or quotes; use AI images or video; copy another creator's script, shots or frames; clone a
real person's voice without their consent (the narrator is an AI reference voice); overwrite a project without asking.
