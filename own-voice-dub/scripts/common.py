"""Shared helpers: load a faster-whisper model on GPU when possible (Windows: borrow PyTorch's CUDA DLLs), else CPU."""
import os, subprocess
from pathlib import Path


def _add_torch_dlls():
    if os.name != 'nt':
        return
    try:
        import torch  # noqa: F401  (loads CUDA libs into the process)
        lib = Path(torch.__file__).parent / 'lib'
        if lib.exists():
            os.add_dll_directory(str(lib))
    except Exception:
        pass


def whisper(name='large-v3-turbo', device='auto'):
    from faster_whisper import WhisperModel
    repo = 'mobiuslabsgmbh/faster-whisper-large-v3-turbo' if name == 'large-v3-turbo' else name
    if device in ('auto', 'cuda'):
        _add_torch_dlls()
        try:
            m = WhisperModel(repo, device='cuda', compute_type='float16')
            import numpy as np
            list(m.transcribe(np.zeros(16000, dtype=np.float32), language='en')[0])  # forces the CUDA libs to load now
            print('whisper: GPU', flush=True); return m
        except Exception as e:
            print(f'whisper: GPU unavailable ({str(e)[:80]}), using CPU', flush=True)
    return WhisperModel(repo, device='cpu', compute_type='int8')


def ffmpeg(*args):
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', *map(str, args)], check=True)


def duration(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(path)], capture_output=True, text=True)
    return float(out.stdout.strip())
