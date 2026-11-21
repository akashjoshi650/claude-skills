"""Hindi narration in an AI voice (Chatterbox multilingual, language 'hi').
One take per script line -> data/takes/sNN.wav, then assembles data/narration.wav + data/lines.json (exact line times).
  VPY tools/hindi_voice.py .            all lines (one take each; tools/best_take.py is better)
  VPY tools/hindi_voice.py . 3,7        re-take lines 3 and 7 (new seed; TAKE=n env for more variants)
  VPY tools/hindi_voice.py . --assemble only re-assemble existing takes
A line's "say" field (if any) is what gets spoken; "text" is what the captions and word check use."""
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import reel_env
reel_env.use_tts_cache()
import torch, torchaudio

P = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
arg = sys.argv[2] if len(sys.argv) > 2 else None
S = json.loads((P / 'script.json').read_text(encoding='utf-8'))
lines = [l['text'] for l in S['lines']]
out = P / 'data/takes'; out.mkdir(parents=True, exist_ok=True)
SR = 24000

if arg != '--assemble':
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    only = [int(x) for x in arg.split(',')] if arg else None
    model = ChatterboxMultilingualTTS.from_pretrained(device=reel_env.device()); SR = model.sr
    ref = str(P / 'data/ref_voice.wav')   # AI reference voice (Kokoro hm_omega sample), not a real person's clone
    for i, s in enumerate(lines):
        if only is not None and i not in only: continue
        text = S['lines'][i].get('say', s)
        torch.manual_seed(2026 + i + (100 if only else 0) + int(os.environ.get('TAKE', 0)) * 1000)
        wav = model.generate(text, language_id='hi', audio_prompt_path=ref, exaggeration=reel_env.EX, cfg_weight=reel_env.CFGW, temperature=reel_env.TEMP)
        torchaudio.save(str(out / f's{i:02d}.wav'), wav.cpu(), SR)
        print(f's{i:02d}: {wav.shape[-1] / SR:.2f}s  {text}', flush=True)

# assemble: lead + takes (silence-trimmed) with gaps + outro; record exact line times
parts, t, meta = [torch.zeros(1, int(S['lead'] * SR))], S['lead'], []
for i, s in enumerate(lines):
    w, r = torchaudio.load(str(out / f's{i:02d}.wav'))
    if r != SR: w = torchaudio.functional.resample(w, r, SR)
    w = w.mean(0, keepdim=True); a = w.abs()[0]; nz = (a > a.max() * 0.02).nonzero()
    if len(nz): w = w[:, max(0, int(nz[0]) - int(0.03 * SR)): int(nz[-1]) + int(0.08 * SR)]
    d = w.shape[-1] / SR
    meta.append({'i': i, 'text': s, 'start': round(t, 3), 'end': round(t + d, 3)})
    gap = S['lines'][i].get('gap', S['gap']) if i < len(lines) - 1 else S['outro']
    parts += [w, torch.zeros(1, int(gap * SR))]; t += d + gap
full = torch.cat(parts, 1)
torchaudio.save(str(P / 'data/narration.wav'), full, SR)
raw = P / 'data/narration_raw.wav'
if raw.exists(): raw.unlink()   # a fresh assembly: speed.py must start again from this one
(P / 'data/lines.json').write_text(json.dumps({'duration': round(full.shape[-1] / SR, 3), 'lines': meta}, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'data/narration.wav: {full.shape[-1] / SR:.2f}s from {len(lines)} lines', flush=True)
