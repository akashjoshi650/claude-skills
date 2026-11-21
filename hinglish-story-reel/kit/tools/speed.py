"""Speed up narration by F (pitch kept, ffmpeg atempo) and scale line/word times. usage: python tools/speed.py . 1.12"""
import json, subprocess, sys, shutil
from pathlib import Path
P, F = Path(sys.argv[1]), float(sys.argv[2])
raw = P / 'data/narration_raw.wav'
if not raw.exists(): shutil.copy(P / 'data/narration.wav', raw)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(raw), '-filter:a', f'atempo={F}', str(P / 'data/narration.wav')], check=True)
L = json.loads((P / 'data/lines.json').read_text(encoding='utf-8'))
if 'speed' not in L:
    L['speed'] = F; L['duration'] = round(L['duration'] / F, 3)
    for l in L['lines']: l['start'] = round(l['start'] / F, 3); l['end'] = round(l['end'] / F, 3)
    W = json.loads((P / 'data/words.json').read_text(encoding='utf-8'))
    for w in W: w['s'] = round(w['s'] / F, 3); w['e'] = round(w['e'] / F, 3)
    (P / 'data/words.json').write_text(json.dumps(W, ensure_ascii=False, indent=1), encoding='utf-8')
    (P / 'data/lines.json').write_text(json.dumps(L, ensure_ascii=False, indent=1), encoding='utf-8')
print('duration', L['duration'])
