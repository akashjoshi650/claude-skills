"""Make N takes of the given lines and keep the one Whisper (with NO hint, so errors show) hears best.
  VPY tools/best_take.py . all [n=3]      every line
  VPY tools/best_take.py . 4,9 [n=3]      only lines 4 and 9 (SEED=k env for a fresh set of seeds)
Writes data/takes/sNN.wav (+ data/takes/try_NN_k.wav for every attempt) and data/bt_log.txt.
Guard: Chatterbox sometimes adds a garbage tail that Whisper doesn't hear. A take that is much longer per word than the
line's other takes is dropped, and when two takes score within 0.03 the shorter one wins."""
import os, sys, json, re, shutil, unicodedata
from pathlib import Path
from difflib import SequenceMatcher
sys.path.insert(0, str(Path(__file__).parent))
import reel_env
reel_env.use_tts_cache()
import torch, torchaudio
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

P = Path(sys.argv[1]); S = json.loads((P / 'script.json').read_text(encoding='utf-8'))
idx = list(range(len(S['lines']))) if sys.argv[2] == 'all' else [int(x) for x in sys.argv[2].split(',')]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 3
SEED = int(os.environ.get('SEED', 0))


def norm(s):
    s = unicodedata.normalize('NFD', s); s = re.sub(r'[़ँंःा-्ॢॣ]', '', s)
    return re.sub(r'[^ऀ-ॿ]', '', s)


tts = ChatterboxMultilingualTTS.from_pretrained(device=reel_env.device())
os.environ.pop('HF_HOME', None)   # Whisper uses the normal Hugging Face cache
from faster_whisper import WhisperModel
wm = WhisperModel('large-v3-turbo', device='cpu', compute_type='int8')
(P / 'data/takes').mkdir(parents=True, exist_ok=True)
log = []
for i in idx:
    txt = S['lines'][i].get('say', S['lines'][i]['text']); nw = len(S['lines'][i]['text'].split()); takes = []
    for k in range(N):
        torch.manual_seed(9000 + i * 10 + k + SEED * 1000)
        w = tts.generate(txt, language_id='hi', audio_prompt_path=str(P / 'data/ref_voice.wav'), exaggeration=reel_env.EX, cfg_weight=reel_env.CFGW, temperature=reel_env.TEMP)
        f = P / f'data/takes/try_{i:02d}_{k}.wav'; torchaudio.save(str(f), w.cpu(), tts.sr); dur = w.shape[-1] / tts.sr
        heard = ' '.join(x.text.strip() for x in wm.transcribe(str(f), language='hi')[0])
        r = SequenceMatcher(None, norm(S['lines'][i]['text']), norm(heard)).ratio()
        takes.append((r, dur, f, heard))
        msg = f'line {i} take {k}: {r:.2f} {dur:.1f}s ({dur / nw:.2f}s/word) | {heard}'; print(msg, flush=True); log.append(msg)
    med = sorted(t[1] for t in takes)[len(takes) // 2]
    ok = [t for t in takes if t[1] <= med * 1.25] or takes   # drop takes with a long hallucinated tail
    top = max(t[0] for t in ok)
    best = min((t for t in ok if t[0] >= top - 0.03), key=lambda t: t[1])
    shutil.copy(best[2], P / f'data/takes/s{i:02d}.wav')
    flag = '' if best[0] >= 0.75 else '   <-- LOW: rewrite the line or retake with SEED=1'
    msg = f'line {i}: kept {best[2].name} ({best[0]:.2f}, {best[1]:.1f}s){flag}'; print(msg, flush=True); log.append(msg)
with open(P / 'data/bt_log.txt', 'a', encoding='utf-8') as fh: fh.write('\n'.join(log) + '\n')
