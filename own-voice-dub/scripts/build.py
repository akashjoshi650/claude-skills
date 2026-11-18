"""Check, time and mux every preset rendered by speak.py.
usage: PY build.py <dub.json> <out_dir> [--whisper small.en]
For each <out_dir>/<preset>/: Whisper re-reads every take (OK / MISMATCH vs the script), trims silence, places each
take at its start time (speeds up at most 1.25x if it would overrun its window), writes <out_dir>/<preset>.wav and
<out_dir>/<preset>.mp4 (original picture copied untouched, new English audio)."""
import argparse, json, re, sys, tempfile
from difflib import SequenceMatcher
from pathlib import Path
import numpy as np
from scipy.io import wavfile
sys.path.insert(0, str(Path(__file__).parent))
from common import whisper, ffmpeg, duration

ap = argparse.ArgumentParser(); ap.add_argument('dub'); ap.add_argument('out'); ap.add_argument('--whisper', default='small.en')
a = ap.parse_args()
dub = json.loads(Path(a.dub).read_text(encoding='utf-8')); out = Path(a.out)
video = dub['video']; total = duration(video); SR = 24000
norm = lambda s: re.sub(r'[^a-z0-9 ]+', '', s.lower()).split()
m = whisper(a.whisper)
bad = 0
for d in sorted(p for p in out.iterdir() if p.is_dir() and list(p.glob('take_*.wav'))):
    mix = np.zeros(int(total * SR) + SR, np.float32)
    print(f'\n== {d.name}', flush=True)
    for i, take in enumerate(dub['takes']):
        f = d / f'take_{i:02d}.wav'
        if not f.exists(): print(f'  take {i}: MISSING'); bad += 1; continue
        heard = ' '.join(s.text.strip() for s in m.transcribe(str(f), language='en')[0])
        score = SequenceMatcher(None, norm(take['text']), norm(heard)).ratio()
        ok = score >= 0.9; bad += not ok
        print(f'  take {i}: {"OK" if ok else "MISMATCH"} ({score:.2f})' + ('' if ok else f'\n    want: {take["text"]}\n    heard: {heard}'), flush=True)
        with tempfile.TemporaryDirectory() as td:
            t = Path(td) / 't.wav'
            ffmpeg('-i', f, '-ac', 1, '-ar', SR, '-af', 'silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse', t)
            room = float(take.get('end', total)) - float(take['start']) - 0.08
            if duration(t) > room:
                k = min(1.25, duration(t) / room); t2 = Path(td) / 's.wav'; ffmpeg('-i', t, '-filter:a', f'atempo={k:.4f}', t2); t = t2
                print(f'    sped up x{k:.2f} to fit {room:.2f}s' + (' (STILL TOO LONG: shorten the text)' if k >= 1.25 else ''))
            _, x = wavfile.read(t); x = x.astype(np.float32) / 32768.0
        s = int((float(take['start']) + 0.05) * SR); mix[s:s + len(x)] += x[:len(mix) - s]
    mix = mix[:int(total * SR)]; mix *= 10 ** (-1 / 20) / (np.abs(mix).max() + 1e-9)
    wavfile.write(out / f'{d.name}.wav', SR, (mix * 32767).astype(np.int16))
    ffmpeg('-i', video, '-i', out / f'{d.name}.wav', '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out / f'{d.name}.mp4')
    print(f'  -> {out / (d.name + ".mp4")}', flush=True)
print(f'\n{"ALL TAKES OK" if not bad else f"{bad} take(s) need a re-render (speak.py --only <preset> --seed <n>)"}')
