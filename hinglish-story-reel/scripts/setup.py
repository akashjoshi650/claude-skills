"""One-time setup for hinglish-story-reel. Safe to re-run.
  python setup.py                         build ~/.hinglish-story-reel/venv (PyTorch + Chatterbox + faster-whisper)
  python setup.py --use-python <python>   reuse a venv that already has Chatterbox (e.g. from own-voice-dub)
               [--hf-home <dir>]          ...and the Hugging Face cache it downloaded the models into
  python setup.py --cpu                   CPU-only PyTorch (works, but each take is slow)
Also finds the faceless-shorts skill (its Tall Tale 3D engine draws the video) and writes ~/.hinglish-story-reel/config.json."""
import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

HOME = Path(os.environ.get('HSR_HOME', Path.home() / '.hinglish-story-reel'))
TORCH = ['torch==2.7.1', 'torchaudio==2.7.1']
# chatterbox-tts 0.1.7 pins torch==2.6.0, which has no kernels for RTX 50-series GPUs: install it with --no-deps
# and add its real dependencies (minus torch/torchaudio and the gradio demo) ourselves.
CHATTERBOX_DEPS = ['numpy>=1.24,<2', 'librosa==0.11.0', 's3tokenizer', 'transformers==5.2.0', 'diffusers==0.29.0',
                   'resemble-perth>=1.0.0', 'conformer==0.3.2', 'safetensors==0.5.3', 'spacy-pkuseg', 'pykakasi==2.3.0',
                   'pyloudnorm', 'omegaconf', 'soundfile', 'scipy']
OTHER = ['faster-whisper']


def run(cmd):
    print('>', ' '.join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True)


def find_faceless():
    """The faceless-shorts skill folder (needs styles/tall-tale/example)."""
    if os.environ.get('FACELESS_SKILL'):
        cands = [Path(os.environ['FACELESS_SKILL'])]
    else:
        roots = [Path.home() / '.claude/skills', Path.home() / '.claude/plugins', Path.cwd() / '.claude/skills']
        cands = [p.parent.parent.parent for r in roots if r.exists() for p in r.glob('**/styles/tall-tale/example')]
    for c in cands:
        if (c / 'styles/tall-tale/example/src/core/toon.js').exists():
            return c.resolve()
    return None


def check(name):
    ok = shutil.which(name) is not None
    print(f'  {name:7s} {"ok" if ok else "MISSING"}')
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--use-python'); ap.add_argument('--hf-home'); ap.add_argument('--cpu', action='store_true')
    a = ap.parse_args()
    HOME.mkdir(parents=True, exist_ok=True)

    print('Tools:')
    missing = [n for n in ('ffmpeg', 'node') if not check(n)]
    if missing:
        sys.exit(f'Install {", ".join(missing)} first (ffmpeg.org, nodejs.org v22+), then re-run.')

    fs = find_faceless()
    if not fs:
        sys.exit('The faceless-shorts skill was not found. It draws the video (Tall Tale 3D engine).\n'
                 'Install it into ~/.claude/skills/faceless-shorts (or set FACELESS_SKILL=<its folder>) and run its\n'
                 'scripts/setup.sh once (it sets up headless Chrome capture), then re-run this.')
    print(f'faceless-shorts: {fs}')

    if a.use_python:
        py = Path(a.use_python).resolve(); hf = Path(a.hf_home).resolve() if a.hf_home else None
    else:
        if not ((3, 10) <= sys.version_info[:2] <= (3, 12)):
            sys.exit(f'Python 3.10-3.12 is needed to build the voice venv, this is {sys.version.split()[0]}')
        hf = HOME / 'hf-cache'; hf.mkdir(exist_ok=True)
        venv = HOME / 'venv'
        if not venv.exists():
            run([sys.executable, '-m', 'venv', str(venv)])
        py = venv / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        run([py, '-m', 'pip', 'install', '--upgrade', 'pip', '-q'])
        gpu = not a.cpu and shutil.which('nvidia-smi') and subprocess.run(['nvidia-smi'], capture_output=True).returncode == 0
        index = 'https://download.pytorch.org/whl/cu128' if gpu else 'https://download.pytorch.org/whl/cpu'
        print(f'PyTorch build: {"CUDA 12.8 (GPU)" if gpu else "CPU"}', flush=True)
        run([py, '-m', 'pip', 'install', *TORCH, '--index-url', index])
        run([py, '-m', 'pip', 'install', 'chatterbox-tts==0.1.7', '--no-deps'])
        run([py, '-m', 'pip', 'install', *CHATTERBOX_DEPS, *OTHER])

    run([py, '-c', 'import torch, scipy, faster_whisper; from chatterbox.mtl_tts import ChatterboxMultilingualTTS; '
                   'print("torch", torch.__version__, "| GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none")'])
    cfg = {'py': str(py), 'hf_home': str(hf) if hf else None, 'faceless': str(fs)}
    (HOME / 'config.json').write_text(json.dumps(cfg, indent=1), encoding='utf-8')
    print(f'\nAll set. Config: {HOME / "config.json"}\n  VPY = {py}\n'
          'Ignore pip\'s "chatterbox-tts requires torch==2.6.0" warning: that is intentional.')


if __name__ == '__main__':
    main()
