"""The whole narration in one go, with the approved settings:
best of 3 takes per line -> assemble -> Hindi word timings + check -> atempo 1.12 -> a report of lines to look at.
  python voice.py <project>              all lines
  python voice.py <project> 4,9          only retake lines 4 and 9 (SEED=1 env for new seeds), then redo the rest
  python voice.py <project> --no-takes   keep the takes, just re-assemble, re-time and re-speed
Long (~1-2 min per line on a GPU). Run it in the background and wait for it to finish."""
import json, os, re, subprocess, sys
from pathlib import Path

HOME = Path(os.environ.get('HSR_HOME', Path.home() / '.hinglish-story-reel'))
cfg = json.loads((HOME / 'config.json').read_text(encoding='utf-8'))
VPY = cfg['py']
P = Path(sys.argv[1]).resolve(); which = sys.argv[2] if len(sys.argv) > 2 else 'all'
env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
T = P / 'tools'


def run(*args):
    print('>', *args, flush=True)
    subprocess.run([VPY, *map(str, args)], check=True, env=env, cwd=P)


S = json.loads((P / 'script.json').read_text(encoding='utf-8'))
if not S['lines']:
    sys.exit('script.json has no lines yet')
for i, l in enumerate(S['lines']):
    if re.search(r'[0-9०-९]', l.get('say', l['text'])):
        print(f'warning: line {i} has digits in the spoken text; write numbers as words (e.g. "एक सौ पचास")')
    if 'roman' not in l and S.get('captions') == 'roman':
        print(f'warning: line {i} has no "roman" caption text')

if which != '--no-takes':
    run(T / 'best_take.py', P, which, os.environ.get('TAKES', 3))
run(T / 'hindi_voice.py', P, '--assemble')
run(T / 'hindi_words.py', P)
run(T / 'speed.py', P, os.environ.get('VSPEED', 1.12))

L = json.loads((P / 'data/lines.json').read_text(encoding='utf-8'))
print(f'\nNarration: {L["duration"]:.1f} s (after x{L.get("speed", 1)})')
check = (P / 'data/check.txt').read_text(encoding='utf-8').splitlines()
for ln, c in zip(L['lines'], check):
    d = ln['end'] - ln['start']; nw = len(S['lines'][ln['i']]['text'].split())
    slow = d / nw > 0.75
    print(('  ' if c.split()[2] == 'OK' and not slow else '! ') + c + (f'   [{d / nw:.2f}s/word: listen for a garbage tail]' if slow else ''))
print('\nCheck every NUMBER in the "heard" text above (Chatterbox misreads some Hindi numbers). Retake bad lines with:\n'
      f'  python "{Path(__file__)}" "{P}" <i,j>')
