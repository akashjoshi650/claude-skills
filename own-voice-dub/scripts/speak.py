"""Speak every take of dub.json in the cloned voice (Chatterbox TTS), once per preset.
usage: PY speak.py <dub.json> <out_dir> [--presets balanced,relaxed,lively] [--custom ex,cfg,temp] [--only preset] [--seed 7]
Writes <out_dir>/<preset>/take_00.wav ... Set HF_HOME so the ~3 GB model is cached where you want it."""
import argparse, json, sys
from pathlib import Path

PRESETS = {'balanced': (0.5, 0.5, 0.8), 'relaxed': (0.65, 0.3, 0.85), 'lively': (0.8, 0.3, 0.9)}

ap = argparse.ArgumentParser(); ap.add_argument('dub'); ap.add_argument('out')
ap.add_argument('--presets', default='lively'); ap.add_argument('--custom'); ap.add_argument('--only'); ap.add_argument('--seed', type=int, default=7)
a = ap.parse_args()
dub = json.loads(Path(a.dub).read_text(encoding='utf-8'))
ref = dub['reference']
if not Path(ref).exists(): sys.exit(f'reference voice sample not found: {ref}')

todo = {}
for p in a.presets.split(','):
    p = p.strip()
    if p:
        if p not in PRESETS: sys.exit(f'unknown preset {p}; choose from {", ".join(PRESETS)} or use --custom')
        todo[p] = PRESETS[p]
if a.custom:
    ex, cfg, temp = map(float, a.custom.split(',')); todo[f'custom_{ex}_{cfg}_{temp}'] = (ex, cfg, temp)
if a.only:
    todo = {k: v for k, v in todo.items() if k == a.only} or ({a.only: PRESETS[a.only]} if a.only in PRESETS else {})
    if not todo: sys.exit(f'--only {a.only}: not a known preset')

import torch, torchaudio
from chatterbox.tts import ChatterboxTTS
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f'chatterbox on {dev}', flush=True)
model = ChatterboxTTS.from_pretrained(device=dev)
for name, (ex, cfg, temp) in todo.items():
    d = Path(a.out) / name; d.mkdir(parents=True, exist_ok=True)
    (d / 'settings.json').write_text(json.dumps({'exaggeration': ex, 'cfg_weight': cfg, 'temperature': temp, 'seed': a.seed}))
    for i, take in enumerate(dub['takes']):
        torch.manual_seed(a.seed + i)
        wav = model.generate(take['text'], audio_prompt_path=ref, exaggeration=ex, cfg_weight=cfg, temperature=temp)
        torchaudio.save(str(d / f'take_{i:02d}.wav'), wav.cpu(), model.sr)
        print(f'{name}/take_{i:02d}: {wav.shape[-1] / model.sr:.2f}s', flush=True)
print('done')
