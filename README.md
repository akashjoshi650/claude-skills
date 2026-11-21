# Claude Skills

A collection of [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) for Claude
(Claude Code, the Claude apps, and the Claude Agent SDK). Each folder is one self-contained skill: a `SKILL.md` with
instructions, plus any scripts it needs.

| Skill | What it does |
|---|---|
| [own-voice-dub](own-voice-dub/) | Dub a video from Hindi (or any language) into English **in your own cloned voice**: local, free, GPU-accelerated. Whisper → translation → Chatterbox voice clone → word check → muxed MP4. Renders A/B/C versions with different voice settings to compare. |
| [hinglish-story-reel](hinglish-story-reel/) | Turn a funny true story (cons, scams, jail escapes, weird history) into a ~70 s **Hindi/Hinglish Instagram Reel**, all in code and free: cartoon people in a 3D world, a smooth Hindi AI narrator (Chatterbox), romanized Hinglish captions, stickers, music and sound effects. The "Natwarlal sold the Taj Mahal" format. Needs the faceless-shorts skill for its Tall Tale 3D engine. |

More skills coming.

## Install a skill

**Claude Code** (personal, all projects): copy the skill folder into your skills directory:

```bash
# macOS / Linux
cp -r own-voice-dub ~/.claude/skills/
```

```powershell
# Windows
Copy-Item -Recurse own-voice-dub "$env:USERPROFILE\.claude\skills\"
```

For one project only, copy it into `<project>/.claude/skills/` instead. Then just ask Claude, e.g.
*"Dub my video C:\Videos\lesson.mkv from Hindi to English in my own voice."*

**Claude.ai / Claude desktop app:** download the skill's zip from [Releases](../../releases) (or zip the folder
yourself so `SKILL.md` sits inside one top-level folder) and upload it under **Settings → Capabilities → Skills**.
Note: `own-voice-dub` runs local models on your GPU, so it needs an environment that can run Python and ffmpeg
on your machine, like Claude Code.

## own-voice-dub: voice settings compared

Same sentence, same 22-second voice sample, three Chatterbox settings:

| Preset | Feel | exaggeration / cfg_weight / temperature |
|---|---|---|
| `balanced` | closest copy of you, calmer | 0.5 / 0.5 / 0.8 |
| `relaxed` | looser, more conversational | 0.65 / 0.3 / 0.85 |
| `lively` | most energy, YouTube-style | 0.8 / 0.3 / 0.9 |

Lessons learned while building it:
- **Generate whole sentences, not phrases.** Phrase-by-phrase generation sounds robotic; one take per sentence flows.
- **Don't denoise the voice sample.** Noise reduction strips breath and texture and makes the clone flatter.
- **Split on real silences.** Whisper's word timestamps run straight through pauses in Hindi, and one long segment
  can get truncated, so the transcriber cuts at silences first and transcribes each chunk.
- **RTX 50-series:** `chatterbox-tts` pins PyTorch 2.6, which has no kernels for these GPUs. The setup script
  installs PyTorch 2.7.1 (CUDA 12.8) and Chatterbox with `--no-deps`.

## hinglish-story-reel: how it works

`script.json` (Devanagari text for the voice + romanized Hinglish for captions) → Chatterbox multilingual in Hindi, 3 takes
per line, the one Whisper hears best is kept → word timings → ffmpeg atempo x1.12 → shots written in code on the Tall Tale
3D engine (from the faceless-shorts skill, installed separately) → procedural music and sound effects → headless Chrome
captures every frame → MP4. Claude reviews a contact sheet of the whole reel before you see it.

Setup: install faceless-shorts and run its `scripts/setup.sh` once, then `python hinglish-story-reel/scripts/setup.py`
(or `--use-python <venv python> --hf-home <cache>` to reuse the own-voice-dub venv). Then ask Claude:
*"Make a Hinglish story reel about Victor Lustig selling the Eiffel Tower."*

Lessons learned:
- **Chatterbox needs Devanagari**, but Instagram audiences read Hinglish faster, so each line has both: `text` for the
  voice and `roman` for the screen. Captions map roman words onto the spoken word times by position.
- **Check every number.** Chatterbox read "तेईस" (23) as 30 and "डेढ़ सौ" (150) as 200. Write numbers as plain words.
- **Whisper without a hint** is the honest check: with the script as `initial_prompt` it "hears" what it was told.
- **Plain ffmpeg atempo** for the speed-up; rubberband added audible reverb.
- The narrator is an AI reference voice (a Kokoro hm_omega sample), not a clone of a real person.

## Responsible use
Only clone your own voice or a voice whose owner clearly agreed. Chatterbox embeds an imperceptible
[Perth](https://github.com/resemble-ai/Perth) watermark in all generated audio.

## Credits
- [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) by Resemble AI (MIT)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT) with OpenAI Whisper `large-v3-turbo`
- [PyTorch](https://pytorch.org), [ffmpeg](https://ffmpeg.org)
- hinglish-story-reel: the Tall Tale 3D engine of the faceless-shorts skill (not included here; installed separately),
  [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) (Apache-2.0) for the narrator reference sample, [three.js](https://threejs.org) (MIT)

## License
MIT. See [LICENSE](LICENSE). The models and libraries above keep their own licenses.
