"""One-time setup for own-voice-dub: a venv with PyTorch (+CUDA when available), Chatterbox TTS and faster-whisper.
usage: python setup.py --dir <folder> [--cpu]
Creates <folder>/venv and <folder>/hf-cache. Re-running is safe (pip skips what is installed)."""
import argparse, os, shutil, subprocess, sys
from pathlib import Path

TORCH = ['torch==2.7.1', 'torchaudio==2.7.1']
# chatterbox-tts 0.1.7 pins torch==2.6.0, which has no kernels for RTX 50-series GPUs, so install it with --no-deps
# and add its real dependencies (minus torch/torchaudio and the gradio demo UI) ourselves.
CHATTERBOX_DEPS = ['numpy>=1.24,<2', 'librosa==0.11.0', 's3tokenizer', 'transformers==5.2.0', 'diffusers==0.29.0',
                   'resemble-perth>=1.0.0', 'conformer==0.3.2', 'safetensors==0.5.3', 'spacy-pkuseg', 'pykakasi==2.3.0',
                   'pyloudnorm', 'omegaconf', 'soundfile', 'scipy']
OTHER = ['faster-whisper']


def run(cmd):
    print('>', ' '.join(map(str, cmd)), flush=True)
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--dir', required=True); ap.add_argument('--cpu', action='store_true')
    a = ap.parse_args()
    if not ((3, 10) <= sys.version_info[:2] <= (3, 12)):
        sys.exit(f'Python 3.10-3.12 needed, this is {sys.version.split()[0]}')
    if not shutil.which('ffmpeg'):
        sys.exit('ffmpeg not found on PATH: install it first (https://ffmpeg.org/download.html)')
    root = Path(a.dir).resolve(); root.mkdir(parents=True, exist_ok=True); (root / 'hf-cache').mkdir(exist_ok=True)
    venv = root / 'venv'
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
    run([py, '-c', 'import torch; print("torch", torch.__version__, "| GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none")'])
    print(f'\nSetup done.\n  PY      = {py}\n  HF_HOME = {root / "hf-cache"}\n'
          'Ignore pip\'s "chatterbox-tts requires torch==2.6.0" warning: that is intentional.')


if __name__ == '__main__':
    main()
