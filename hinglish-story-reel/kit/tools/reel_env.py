"""Shared settings for the Hindi voice tools. Written by the skill's setup.py to ~/.hinglish-story-reel/config.json.
The approved narrator: Chatterbox multilingual, language 'hi', reference = data/ref_voice.wav (a Kokoro hm_omega sample),
exaggeration 0.75, cfg 0.35, temperature 0.85, then ffmpeg atempo 1.12. Override with VEX / VCFG / VTEMP env vars."""
import json, os
from pathlib import Path

CONFIG = Path(os.environ.get('HSR_HOME', Path.home() / '.hinglish-story-reel')) / 'config.json'
CFG = json.loads(CONFIG.read_text(encoding='utf-8')) if CONFIG.exists() else {}

EX = float(os.environ.get('VEX', 0.75))
CFGW = float(os.environ.get('VCFG', 0.35))
TEMP = float(os.environ.get('VTEMP', 0.85))
SPEED = float(os.environ.get('VSPEED', 1.12))


def use_tts_cache():
    """Point Hugging Face at the Chatterbox model cache made by setup.py (if any)."""
    if CFG.get('hf_home'):
        os.environ['HF_HOME'] = CFG['hf_home']


def device():
    import torch
    return 'cuda' if torch.cuda.is_available() else 'cpu'
