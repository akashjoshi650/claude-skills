---
name: own-voice-dub
description: Dub a video from any spoken language (Hindi, Hinglish, Spanish...) into English in the speaker's OWN cloned voice, fully local and free. Transcribes with Whisper, translates, clones the voice from a short sample with Chatterbox (MIT), checks every line, and puts the new audio on the original video. Can render A/B/C versions with different voice settings to compare. Use when someone wants to translate or dub their video or audio into English, keep their own voice, clone their voice for narration, or compare voice-cloning settings.
---

# Own-Voice Dub

Turn a video where someone speaks language X into the same video speaking **English in their own voice**.
Everything runs on the user's computer: no API keys, no uploads, no cost.

`SKILL` = the folder this file is in. Scripts are in `SKILL/scripts/`.

| step | tool | script |
|---|---|---|
| 1. transcribe the original speech | faster-whisper `large-v3-turbo` | `transcribe.py` |
| 2. translate to natural spoken English | you (Claude) | writes `dub.json` |
| 3. clone the voice and speak English | Chatterbox TTS (Resemble AI, MIT) | `speak.py` |
| 4. check words, time to the video, mux | faster-whisper + ffmpeg | `build.py` |

## Consent first
Only clone the voice of the person asking, or someone who clearly agreed. If the video's speaker is someone else
(a celebrity, a client, a stranger) and consent isn't clear, ask before cloning. Chatterbox adds an inaudible
Perth watermark to everything it generates; mention this when sharing results.

## 0. Setup (once per computer)
Needs Python 3.10-3.12, ffmpeg on PATH, ~7 GB of disk. An NVIDIA GPU is strongly recommended (CPU works, slowly).
Ask the user where to keep the environment (default: a `voice-dub` folder in their working directory), then:

```
python SKILL/scripts/setup.py --dir <folder>
```

It creates `<folder>/venv`, installs PyTorch (CUDA 12.8 build when `nvidia-smi` finds a GPU, which also works on
RTX 50-series cards that the PyTorch 2.6 pinned by chatterbox-tts cannot run on), then chatterbox-tts with `--no-deps`
plus its real dependencies, and faster-whisper. Tell the user the download size up front (~3 GB PyTorch + ~3 GB
Chatterbox model on first run + ~1.6 GB Whisper model) and get their OK before running it.
Afterwards use `<folder>/venv/Scripts/python.exe` (Windows) or `<folder>/venv/bin/python` as `PY`, and set
`HF_HOME=<folder>/hf-cache` for every script so all models stay in that folder.

## 1. Transcribe
```
PY SKILL/scripts/transcribe.py <video> <work>/transcript.json --lang hi
```
`--lang` = the spoken language code (`hi` Hindi, `es` Spanish, ...). Always pass it: auto-detection often labels Hindi
as Urdu and writes it in the wrong script. Output: phrases with start/end times, split at natural pauses.
Read the transcript and the video length it prints.

## 2. Translate -> `dub.json`
Translate the MEANING into natural spoken English, the way the speaker would say it to a friend; don't translate
word for word. Then group phrases into **takes**: one take = one full sentence or thought, 5-15 s of speech.
Whole sentences in one take sound natural; phrase-by-phrase generation sounds robotic. Each take starts where the
speaker started that sentence and must end before the next take starts.

```json
{
  "video": "C:/path/original.mkv",
  "reference": "<work>/voice.wav",
  "takes": [
    { "start": 1.04, "end": 14.38, "text": "So, let's get started. I'll do my best to explain everything from the basics." },
    { "start": 14.38, "end": 24.10, "text": "I'll really try to get you doing it yourself." }
  ]
}
```
English usually needs fewer seconds than Hindi, so takes normally fit. If a take is clearly too long for its window,
shorten the wording rather than relying on speed-up (`build.py` speeds up at most 1.25x).

Show the user the transcript next to your translation in a table and let them correct it before generating.

## 3. Voice sample
Cut 15-30 s of continuous, clean speech from the video (or a separate recording) as the reference:
```
ffmpeg -ss <a> -to <b> -i <video> -vn -ac 1 -ar 24000 -af "highpass=f=60,loudnorm=I=-18:TP=-2" <work>/voice.wav
```
Do NOT denoise it (afftdn and similar strip breath and texture and make the clone flatter). Avoid music and keyboard
noise. The clone carries the speaker's accent; a sample in English or a mixed language sounds most natural in English.

## 4. Speak
```
PY SKILL/scripts/speak.py <work>/dub.json <work>/out --presets balanced,relaxed,lively
```
Presets (exaggeration / cfg_weight / temperature):

| preset | feel | settings |
|---|---|---|
| `balanced` | closest copy, calm | 0.5 / 0.5 / 0.8 |
| `relaxed` | looser, conversational | 0.65 / 0.3 / 0.85 |
| `lively` | most energy, YouTube-style | 0.8 / 0.3 / 0.9 |

First time with a new voice: render all three and let the user pick. After that, render only the chosen preset.
Custom settings: `--custom 0.7,0.35,0.85`.

## 5. Build and check
```
PY SKILL/scripts/build.py <work>/dub.json <work>/out
```
For each preset it re-transcribes every take with Whisper and prints `OK` or `MISMATCH` against the script, trims
silence, places each take at its start time, writes `<preset>.wav`, and muxes `<preset>.mp4` with the original
picture copied untouched (`-c:v copy`). Any MISMATCH: re-run `speak.py` with `--only <preset> --seed <n>` and rebuild.
Never deliver a take that failed the check.

## 6. Deliver
Give the user the MP4(s) with full paths, the transcript/translation table, and which settings made each version.
You cannot hear audio: say so, and let the user judge which version sounds most like them. If every version sounds
robotic, the fix is almost always a better sample (step 3), not more settings.

## Troubleshooting
- `cublas64_12.dll not found` (Whisper on GPU, Windows): `transcribe.py` and `build.py` already add PyTorch's CUDA
  folder to the DLL search path and fall back to CPU; CPU is fine for short clips.
- `CUDA error: no kernel image is available`: PyTorch is too old for the GPU; re-run setup (it installs the cu128 build).
- Phrases too long or too short in the transcript: `transcribe.py` splits at silences; use `--silence -30` (noisy
  room) or `-40` (quiet room), and `--pause 0.4` for fewer, longer phrases.
- Garbled or repeated words: lower `temperature` (0.7) or `exaggeration`; try another `--seed`.
- Hugging Face symlink warning on Windows: harmless.

## Credits
Chatterbox TTS by Resemble AI (MIT) · faster-whisper / OpenAI Whisper (MIT) · ffmpeg.
