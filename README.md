# Claude Skills

A collection of [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) for Claude
(Claude Code, the Claude apps, and the Claude Agent SDK). Each folder is one self-contained skill: a `SKILL.md` with
instructions, plus any scripts it needs.

| Skill | What it does |
|---|---|
| [own-voice-dub](own-voice-dub/) | Dub a video from Hindi (or any language) into English **in your own cloned voice**: local, free, GPU-accelerated. Whisper → translation → Chatterbox voice clone → word check → muxed MP4. Renders A/B/C versions with different voice settings to compare. |

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

## Responsible use
Only clone your own voice or a voice whose owner clearly agreed. Chatterbox embeds an imperceptible
[Perth](https://github.com/resemble-ai/Perth) watermark in all generated audio.

## Credits
- [Chatterbox TTS](https://github.com/resemble-ai/chatterbox) by Resemble AI (MIT)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (MIT) with OpenAI Whisper `large-v3-turbo`
- [PyTorch](https://pytorch.org), [ffmpeg](https://ffmpeg.org)

## License
MIT. See [LICENSE](LICENSE). The models and libraries above keep their own licenses.
