"""Hindi word timings + take check with faster-whisper large-v3-turbo (CPU) -> data/words.json [{w, line, s, e}].
Each take is transcribed with word timestamps; script words keep their spelling and get the times of the heard words
they match (Devanagari compared letter by letter, matras/nukta ignored). Unmatched words share the gap by length.
Prints a match score per line (BAD < 0.6 = re-take that line).
  VPY tools/hindi_words.py ."""
import sys, json, re, unicodedata
from pathlib import Path
from difflib import SequenceMatcher
from faster_whisper import WhisperModel

P = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
LJ = json.loads((P / 'data/lines.json').read_text(encoding='utf-8'))
S = json.loads((P / 'script.json').read_text(encoding='utf-8'))

def norm(w):
    w = unicodedata.normalize('NFD', w)
    w = re.sub(r'[़ँंःा-्ॢॣ]', '', w)   # drop nukta, nasal marks, vowel signs, virama
    return re.sub(r'[^ऀ-ॿa-z0-9]', '', w.lower())

m = WhisperModel('large-v3-turbo', device='cpu', compute_type='int8')
words, report = [], []
for ln in LJ['lines']:
    i, t0, t1 = ln['i'], ln['start'], ln['end']
    sw = S['lines'][i]['text'].split()
    segs, _ = m.transcribe(str(P / f'data/takes/s{i:02d}.wav'), language='hi', word_timestamps=True, initial_prompt=S['lines'][i]['text'])
    heard = [(x.word.strip(), x.start, x.end) for sg in segs for x in sg.words]
    # take times are relative to the raw take; the assembly trimmed leading silence, so shift by first-word onset
    off = t0 - (heard[0][1] if heard else 0) + 0.03 if heard else t0
    a, b = [norm(w) for w in sw], [norm(h[0]) for h in heard]
    times = [None] * len(a)
    for blk in SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks():
        for k in range(blk.size): times[blk.a + k] = (heard[blk.b + k][1] + off, heard[blk.b + k][2] + off)
    k = 0
    while k < len(a):
        if times[k]: k += 1; continue
        j = k
        while j < len(a) and not times[j]: j += 1
        lo = times[k - 1][1] if k else t0; hi = times[j][0] if j < len(a) else t1
        if hi <= lo: hi = lo + 0.1 * (j - k)
        L = [max(1, len(a[q])) for q in range(k, j)]; c = lo
        for q, l in zip(range(k, j), L): d = (hi - lo) * l / sum(L); times[q] = (c, c + d * 0.9); c += d
        k = j
    for w, (s, e) in zip(sw, times): words.append({'w': w, 'line': i, 's': round(max(t0, min(s, t1)), 3), 'e': round(max(t0, min(e, t1)), 3)})
    raw = ' '.join(x.text.strip() for x in m.transcribe(str(P / f'data/takes/s{i:02d}.wav'), language='hi')[0])   # no hint: honest check
    r = SequenceMatcher(None, ''.join(a), ''.join(norm(w) for w in raw.split())).ratio(); heard = [(raw, 0, 0)]
    report.append(f'line {i:2d} {"OK " if r >= 0.6 else "BAD"} {r:.2f} | heard: {" ".join(h[0] for h in heard)}')
(P / 'data/words.json').write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding='utf-8')
(P / 'data/check.txt').write_text('\n'.join(report), encoding='utf-8')
print('\n'.join(report)); print(f'data/words.json: {len(words)} words')
