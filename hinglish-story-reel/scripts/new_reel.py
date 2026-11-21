"""Start a new reel project: the faceless-shorts Tall Tale 3D engine + this skill's Hindi kit + the approved voice.
  python new_reel.py <short-name> [--dir <parent>] [--blank]
--dir defaults to the current folder. Without --blank the project starts from the example reel (script.json + shots.js
of "Bihar ka Nakli Thana"), so you can see the patterns; rewrite both for the new story."""
import argparse, json, os, shutil, sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
HOME = Path(os.environ.get('HSR_HOME', Path.home() / '.hinglish-story-reel'))


def patch(path, pairs):
    s = path.read_text(encoding='utf-8')
    for old, new in pairs:
        if new in s: continue
        if old not in s:
            print(f'  warning: could not patch {path.name} ({old[:40]!r} not found); check it by hand'); continue
        s = s.replace(old, new, 1)
    path.write_text(s, encoding='utf-8', newline='')   # keep LF line endings


EXTRA_FX = '''def rev(d=1.0, **_):
    t = tt(d); f = 70 + 150 * (1 - np.exp(-t * 3)) + 12 * np.sin(2 * np.pi * 9 * t)
    ph = np.cumsum(f) / SR; x = sum(np.sign(np.sin(2 * np.pi * ph * h)) / h for h in (1, 2, 3)) * 0.3 + bp(noise(d), 200, 1500) * 0.15
    return lp(x, 2200) * np.minimum(1, t / 0.05) * np.minimum(1, (d - t) / 0.25)
def sputter(d=1.2, **_):
    x = np.zeros(int(d * SR))
    for k, st in enumerate(np.arange(0, d - 0.15, 0.13)):
        i = int(st * SR); n = int(0.07 * SR); x[i:i + n] += bp(noise(0.07), 120, 900) * env(n, 0.002, 4) * (1 - st / d) * (0.4 if k % 3 == 2 else 1)
    return x * 0.9
def levelup(**_):
    x = np.zeros(int(0.9 * SR))
    for k, f in enumerate([523.3, 659.3, 784.0, 1046.5]):
        i = int(k * 0.08 * SR); n = int(0.5 * SR); x[i:i + n] += (np.sin(2 * np.pi * f * tt(0.5)) + 0.4 * np.sin(4 * np.pi * f * tt(0.5))) * env(n, 0.003, 5) * 0.3
    return lp(x, 4500)

FX = dict(rev=rev, sputter=sputter, levelup=levelup, '''


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('name'); ap.add_argument('--dir', default='.'); ap.add_argument('--blank', action='store_true')
    a = ap.parse_args()
    cfgf = HOME / 'config.json'
    if not cfgf.exists():
        sys.exit(f'Run setup first: python "{SKILL / "scripts/setup.py"}"')
    cfg = json.loads(cfgf.read_text(encoding='utf-8'))
    src = Path(cfg['faceless']) / 'styles/tall-tale/example'
    dst = Path(a.dir).resolve() / a.name
    if dst.exists():
        sys.exit(f'{dst} already exists: pick another name')

    shutil.copytree(src, dst)
    shutil.copytree(SKILL / 'kit', dst, dirs_exist_ok=True)                       # Hindi captions + voice tools
    patch(dst / 'src/core/timing.js', [("replace(/[^a-z0-9']+/g, '')", "replace(/[^a-z0-9'ऀ-ॣ०-ॿ]+/g, '')")])
    patch(dst / 'tools/mix.py', [("(P / 'data/cues.json').read_text())", "(P / 'data/cues.json').read_text(encoding='utf-8'))"),
                                 ("(P / 'script.json').read_text())", "(P / 'script.json').read_text(encoding='utf-8'))"),
                                 ('FX = dict(', EXTRA_FX),
                                 ('LEVEL = dict(', 'LEVEL = dict(rev=-17, sputter=-15, levelup=-14, ')])
    for f in ('lines.json', 'words.json', 'words.txt', 'cues.json', 'narration.wav', 'mix.wav'):
        (dst / 'data' / f).unlink(missing_ok=True)                                # those belong to the English example
    for d in ('data/takes', 'renders', 'review'):
        (dst / d).mkdir(parents=True, exist_ok=True)
    shutil.copy(SKILL / 'assets/ref_voice.wav', dst / 'data/ref_voice.wav')       # the approved narrator reference
    if a.blank:
        (dst / 'script.json').write_text(json.dumps({'title': a.name, 'captions': 'roman', 'lead': 0.3, 'outro': 1.2, 'gap': 0.18,
                                                     'music': 'bounce', 'sources': [], 'lines': []}, indent=1), encoding='utf-8')
    else:
        shutil.copy(SKILL / 'example/script.json', dst / 'script.json')
        shutil.copy(SKILL / 'example/shots.js', dst / 'src/shots.js')
    print(dst)
    print(f'VPY = {cfg["py"]}\nNext: write script.json, then python "{SKILL / "scripts/voice.py"}" "{dst}"')


if __name__ == '__main__':
    main()
