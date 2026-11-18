"""Transcribe the speech in a video/audio file into phrases split at real pauses.
usage: PY transcribe.py <media> <out.json> --lang hi [--model large-v3-turbo] [--silence -35] [--pause 0.25]
Finds pauses with ffmpeg silencedetect (Whisper's own word times run through pauses, and one long segment can get
truncated), then transcribes each speech chunk on its own. Writes {"duration", "lang", "phrases": [{start, end, text}]}."""
import argparse, json, re, subprocess, sys, tempfile
from pathlib import Path
import numpy as np
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).parent))
from common import whisper, ffmpeg, duration

ap = argparse.ArgumentParser(); ap.add_argument('media'); ap.add_argument('out'); ap.add_argument('--lang', required=True)
ap.add_argument('--model', default='large-v3-turbo'); ap.add_argument('--silence', type=float, default=-35)
ap.add_argument('--pause', type=float, default=0.25); ap.add_argument('--min-chunk', type=float, default=1.2)
a = ap.parse_args()

total = duration(a.media)
with tempfile.TemporaryDirectory() as td:
    wav = Path(td) / 'a.wav'; ffmpeg('-i', a.media, '-vn', '-ac', 1, '-ar', 16000, '-af', 'loudnorm=I=-20', wav)
    sd = subprocess.run(['ffmpeg', '-i', str(wav), '-af', f'silencedetect=noise={a.silence}dB:d={a.pause}', '-f', 'null', '-'], capture_output=True, text=True).stderr
    sr, x = wavfile.read(wav)
x = x.astype(np.float32) / 32768.0
starts = [float(v) for v in re.findall(r'silence_start: ([\d.]+)', sd)]; ends = [float(v) for v in re.findall(r'silence_end: ([\d.]+)', sd)]
# speech chunks = the gaps between silences
chunks, t = [], 0.0
for s, e in zip(starts, ends + [total] * (len(starts) - len(ends))):
    if s - t > 0.15: chunks.append([t, s])
    t = e
if total - t > 0.15: chunks.append([t, total])
merged = []                                   # glue very short chunks onto the previous one
for c in chunks:
    if merged and (c[1] - c[0] < a.min_chunk or merged[-1][1] - merged[-1][0] < a.min_chunk) and c[0] - merged[-1][1] < 0.6:
        merged[-1][1] = c[1]
    else: merged.append(c)

m = whisper(a.model)
phrases = []
for s, e in merged:
    seg = x[max(0, int((s - 0.1) * sr)):int((e + 0.1) * sr)]
    text = ' '.join(z.text.strip() for z in m.transcribe(seg, language=a.lang, vad_filter=False, beam_size=5, condition_on_previous_text=False)[0]).strip()
    if text: phrases.append({'start': round(s, 2), 'end': round(e, 2), 'text': text})
Path(a.out).write_text(json.dumps({'duration': round(total, 2), 'lang': a.lang, 'phrases': phrases}, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'{a.out}: {len(phrases)} phrases, media {total:.2f}s (read the JSON file for the text; consoles may not show the script)')
