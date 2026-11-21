// Captions: ONE word at a time (short words ride along with the next: "a single", "the whole"), white heavy sans with
// a black outline and a soft drop shadow, centre of the screen. No colour highlight. Words keep their punctuation.
// A script line may set "caps": "He bet | his life | savings" to choose the chunks; otherwise they're made automatically.
import { ctx, clamp, lerp, seg, eob } from './lib.js';
import { T, lineWords } from './timing.js';

export const CAP = { y: 1450, size: 96, maxW: 960 };
let caps = [];
const SHORT = /^(का|की|के|है|हैं|में|को|से|ने|ही|तो|भी|और|या|था|पास|ka|ki|ke|hai|hain|mein|ko|se|ne|hi|to|bhi|ya|tha|pe)[,.!?।]*$/i;
let ROMAN = false;   // Hindi particles ride along with the word before them

function autoChunks(ws) {
  const out = [];
  for (let i = 0; i < ws.length; i++) {
    const w = ws[i];
    let j = i; while (j + 1 < ws.length && SHORT.test(ws[j + 1]) && !/[,.!?;:।]$/.test(ws[j]) && j - i < 2) j++;
    out.push([i, j]); i = j;
  }
  return out;
}

export function buildCaptions(script) {
  caps = [];
  script.lines.forEach((ln, i) => {
    const ws = lineWords(i); if (!ws.length) return;
    const textWords = ln.text.split(/\s+/).filter(Boolean);
    const spoken = ws.length === textWords.length ? textWords : ws.map((w) => w.w);
    if (script.captions === 'roman' && ln.roman) {
      // romanized Hinglish: roman word k takes the time of spoken word round(k * m / n) (the two lists run nearly word for word)
      ROMAN = true; const R = ln.roman.split(/\s+/).filter(Boolean), n = R.length, m = ws.length;
      autoChunks(R).forEach(([a, b]) => caps.push({ line: i, s: ws[Math.min(m - 1, Math.round(a * m / n))].s - 0.03, text: R.slice(a, b + 1).join(' ') }));
    } else if (ln.caps) {
      const nm = (w) => String(w).toLowerCase().replace(/[^a-z0-9']+/g, '');
      let from = 0;
      ln.caps.split('|').map((c) => c.trim()).filter(Boolean).forEach((c, j) => {
        const first = nm(c.split(/\s+/)[0]);
        let idx = j === 0 ? 0 : ws.findIndex((w, k) => k > from && nm(w.w) === first);
        if (idx < 0) idx = Math.min(ws.length - 1, from + 1);
        from = idx; caps.push({ line: i, s: ws[idx].s - 0.03, text: c.replace(/\*/g, '') });
      });
    } else autoChunks(spoken).forEach(([a, b]) => caps.push({ line: i, s: ws[a].s - 0.03, text: spoken.slice(a, b + 1).join(' ') }));
  });
  caps.forEach((c) => { c.text = c.text.replace(/[,.!?;:।"“”‘’]/g, '').replace(/\s+/g, ' ').trim(); });
  caps.forEach((c, k) => { const next = caps[k + 1], lineEnd = T.lines[c.line].end; c.e = next ? (next.s - lineEnd > 0.6 && next.line !== c.line ? lineEnd + 0.25 : next.s) : T.dur; });
  return caps;
}
export const captionList = () => caps.map((c) => ({ ...c, words: [{ txt: c.text }] }));

/** draw one caption text at x, y (also used by the style sheet) */
export function captionText(text, x = 540, y = CAP.y, sc = 1) {
  const size = CAP.size;
  ctx.save(); ctx.font = ROMAN ? `900 ${size}px Inter` : `700 ${size}px "Nirmala UI", Inter`; ctx.letterSpacing = '0px';
  const fit = Math.min(1, CAP.maxW / ctx.measureText(text).width);
  ctx.translate(x, y); ctx.scale(sc * fit, sc * fit); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
  ctx.fillStyle = 'rgba(0,0,0,0.45)'; ctx.fillText(text, 3, 9);
  ctx.lineWidth = 15; ctx.strokeStyle = '#0B0B10'; ctx.strokeText(text, 0, 0);
  ctx.fillStyle = '#FFFFFF'; ctx.fillText(text, 0, 0);
  ctx.restore();
}
export function drawCaption(t) {
  const c = caps.find((c) => t >= c.s && t < c.e); if (!c) return;
  const lt = t - c.s; captionText(c.text, 540, CAP.y, lt < 0.1 ? lerp(0.86, 1, eob(seg(lt, 0, 0.1))) : 1);
}
