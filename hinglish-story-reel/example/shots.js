// BIHAR KA NAKLI THANA — a fake police station in a Banka guest house, 500 m from the real one (Aug 2022).
// Tall Tale 3D cartoon, Hindi roast narration, romanized Hinglish captions + stickers. Original art only.
import * as THREE from 'three';
import { ctx, clamp, lerp, seg, eo, eio, eob } from './core/lib.js';
import { L, Le, Wd, T } from './core/timing.js';
import { camera } from './core/engine.js';
import * as WD from './core/world.js';
import * as PR from './core/props.js';
import { Toon, PROPS, INK } from './core/toon.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const mix = (a, b, k) => a.clone().lerp(b, k);
const F = 'Inter';
const blinkAt = (t, off = 0) => (((t + off) % 3.1) < 0.12 ? 1 : 0);
const talk = (on, t) => (on ? 0.25 + 0.75 * Math.abs(Math.sin(t * 13)) : 0);
const KHAKI = '#C2A66A';
const LOOK = {
  madam: { body: KHAKI, pattern: 'plain', neck: 'collar', neckCol: '#A88E58', hat: 'mailcap', hatCol: '#22222A', hairCol: '#1E1612', head: '#E8B48C', extra: ['blush'] },
  sahab: { body: KHAKI, pattern: 'plain', neck: 'tie', neckCol: '#7A6438', hat: 'mailcap', hatCol: '#8A7440', hairCol: '#1E1612', head: '#E2AE86', extra: ['mustache', 'glasses'] },
  villager: { body: '#E8E0C8', pattern: 'plain', neck: 'scarf', neckCol: '#D85A3A', hat: 'none', hairCol: '#2A1C16', head: '#D9A07A', extra: ['mustache'] },
  shambhu: { body: '#A88A4A', pattern: 'plain', neck: 'collar', neckCol: '#8A7038', hat: 'mailcap', hatCol: '#5A4A30', hairCol: '#1E1612', head: '#D8A47C', extra: ['mustache'] },
  bhola: { body: '#F4F2EC', pattern: 'plain', neck: 'scarf', neckCol: '#E8B04A', hat: 'none', hairCol: '#1E1612', head: '#E0AA80', extra: ['mustache'] },
  dukaan: { body: '#5FA39A', pattern: 'check', patCol: '#3E7F77', hat: 'none', hairCol: '#2A1C16', head: '#ECC09A', extra: ['glasses'] },
};
const person = (k, o) => new Toon({ ...LOOK[k], extra: [...(LOOK[k].extra || [])] }, o);
const M = (col, o = {}) => new THREE.MeshStandardMaterial({ color: col, roughness: 0.8, ...o });
const box = (w, h, d, m, x, y, z, parent) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), typeof m === 'string' ? M(m) : m); b.position.set(x, y, z); b.castShadow = b.receiveShadow = true; parent.add(b); return b; };
// 2D hand props
const KATTA = (g, x, y) => { g.save(); g.translate(x + 6, y - 40); g.rotate(0.15); g.fillStyle = '#4A4A50'; g.strokeStyle = INK; g.lineWidth = 6; g.beginPath(); g.rect(-10, -14, 96, 22); g.fill(); g.stroke(); g.fillStyle = '#7A4A2A'; g.beginPath(); g.moveTo(-10, -2); g.lineTo(18, 8); g.lineTo(6, 60); g.lineTo(-24, 54); g.closePath(); g.fill(); g.stroke(); g.restore(); };
const FORM = PROPS.paper('FORM');

export function buildShots(E) {
  const S = [], CUES = [], add = (o) => (S.push(o), o), cue = (t, type, o = {}) => CUES.push({ t: +t.toFixed(3), type, ...o });
  const cut = (i) => (i === 0 ? 0 : L(i) - 0.06);
  const cam = camera(38);
  const LK = { bloom: 0.22, bloomThreshold: 0.95, aperture: 0.001, maxblur: 0.008, exposure: 1.05, vignette: 0.3 };
  const shoot = (scene, people, from, to, at, k, look = {}) => {
    cam.position.copy(mix(from, to, k)); cam.lookAt(at); cam.updateMatrixWorld();
    people.forEach((p) => p.face(cam));
    E.render(scene, cam, { ...LK, focus: cam.position.distanceTo(at), ...look });
  };
  const proj = (v) => { const p = v.clone().project(cam); return [(p.x + 1) / 2 * 1080, (1 - p.y) / 2 * 1920]; };
  const pop = (t, t0, d = 0.25) => (t < t0 ? 0 : eob(clamp((t - t0) / d)));
  const jolt = (t, t0) => (t >= t0 && t < t0 + 0.35 ? Math.sin((t - t0) * 70) * 16 * (1 - (t - t0) / 0.35) : 0);

  // ── SET 1: Banka street — fake thana (guest house, near) and the real thana (far down the road) ──
  const SR = new THREE.Scene();
  WD.sky(SR, { top: '#4C97E6', horizon: '#F2E2C4' });
  WD.sunlight(SR, E, { pos: [9, 13, 6], box: 14, target: [-2, 0, -10] });
  WD.clouds(SR, [[-40, 40, -150, 18], [30, 52, -160, 22], [70, 34, -140, 12]]);
  { const gr = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), M('#B8A07A')); gr.rotation.x = -Math.PI / 2; gr.receiveShadow = true; SR.add(gr);
    const road = new THREE.Mesh(new THREE.PlaneGeometry(7, 140), WD.mat({ map: WD.T.dirt('#C9A57A', [2, 30]) })); road.rotation.x = -Math.PI / 2; road.position.set(0, 0.01, -50); road.receiveShadow = true; SR.add(road);
    // filler buildings both sides
    const cols = ['#E8C26A', '#9FC9A8', '#E89A7A', '#C9B4E0', '#F2E6CF', '#8FB8D8'];
    for (let i = 0; i < 12; i++) [-1, 1].forEach((s) => { const z = -18 - i * 8, h = 4 + ((i * 7 + (s > 0 ? 3 : 0)) % 5); if (s < 0 && (i === 3 || i === 4)) return; box(6, h, 7.4, cols[(i + (s > 0 ? 2 : 0)) % cols.length], s * 8, h / 2, z, SR); });
    for (let z = -4; z > -110; z -= 12) [-1, 1].forEach((s) => { const p = WD.pole(7); p.position.set(s * 4.2, 0, z); SR.add(p); });
  }
  // the guest house (left, front faces +x toward the road)
  const GH = new THREE.Group(); GH.position.set(-7.5, 0, -8); SR.add(GH);
  box(6, 7.5, 9, '#E9A3AE', 0, 3.75, 0, GH); box(6.4, 0.3, 9.4, '#B8606E', 0, 7.6, 0, GH);
  for (let y of [2, 4.4, 6.4]) for (let z of [-3, -1, 1, 3]) { if (y === 2 && Math.abs(z) < 2) continue; const w = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 1.1), M('#2E4A66', { roughness: 0.3 })); w.position.set(3.01, y, z); w.rotation.y = Math.PI / 2; GH.add(w); }
  { const door = new THREE.Mesh(new THREE.PlaneGeometry(1.8, 2.4), M('#5A3A2A')); door.position.set(3.02, 1.2, 0); door.rotation.y = Math.PI / 2; GH.add(door);
    const sb = WD.signBoard('ANURAG GUEST HOUSE', { w: 4.6, h: 0.8, bg: '#2E4E8A', fg: '#FFFFFF', font: F }); sb.position.set(3.1, 5.4, 0); sb.rotation.y = Math.PI / 2; GH.add(sb);
    const tb = WD.signBoard('THANA', { w: 2.0, h: 0.6, bg: '#B5372E', fg: '#FFFFFF', font: F }); tb.position.set(3.1, 2.95, 0); tb.rotation.y = Math.PI / 2; tb.rotation.z = 0.06; GH.add(tb); }
  // the real thana (right, far)
  const RT = new THREE.Group(); RT.position.set(-8, 0, -50); SR.add(RT);
  box(6, 8, 10, '#F2EEE4', 0, 4, 0, RT); box(6.2, 1.0, 10.2, '#B5372E', 0, 8.3, 0, RT); box(6.05, 0.6, 10.05, '#2E4E8A', 0, 1.0, 0, RT);
  { const sb = WD.signBoard('POLICE STATION', { w: 7, h: 1.6, bg: '#2E4E8A', fg: '#FFFFFF', font: F }); sb.position.set(1.5, 10.0, 0); sb.rotation.y = 0.12; RT.add(sb); }
  const madS = person('madam', { height: 1.62 }), sahS = person('sahab', { height: 1.74 }), bholaS = person('bhola', { height: 1.7 }), vilS = person('villager', { height: 1.68 });
  SR.add(madS.group, sahS.group, bholaS.group, vilS.group);

  // ── SET 2: inside the fake thana (a guest-house room) ──
  const TH = WD.interior(E, { wall: '#D9C99E', motif: '#D0BF92', floor: '#8A7A6A', ceiling: '#4A5A50', signText: 'THANA · ROOM NO. 4', counterOn: false, litter: false, picture: false });
  const dsk = PR.desk(1.8); dsk.position.set(0, 0, -3.9); TH.scene.add(dsk);
  const stackTex = (() => { const c = document.createElement('canvas'); c.width = 128; c.height = 512; const g = c.getContext('2d'); for (let y = 0; y < 512; y += 8) { g.fillStyle = ['#F4EFE4', '#E9E2D2', '#FFFDF4', '#F2D9A8', '#DDE8F0'][(y / 8) % 5]; g.fillRect(0, y, 128, 8); g.fillStyle = '#B8B0A0'; g.fillRect(0, y + 7, 128, 1); } const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t; })();
  const stack = box(0.42, 1, 0.32, M('#FFFFFF', { map: stackTex }), 0.6, 0.86, -3.75, TH.scene); stack.scale.y = 0.02;
  { const flagC = WD.signBoard('NYAY · SEVA · SURAKSHA', { w: 2.6, h: 0.42, bg: '#F2C230', fg: '#1F1C33', font: F }); flagC.position.set(0, 3.0, -6.85); TH.scene.add(flagC); }
  const madT = person('madam', { height: 1.62 }), sahT = person('sahab', { height: 1.74 }), vilT = person('villager', { height: 1.68 }), bholaT = person('bhola', { height: 1.7 });
  TH.scene.add(madT.group, sahT.group, vilT.group, bholaT.group);

  // ── SET 3: the mall ──
  const ML = WD.interior(E, { wall: '#A9D3E8', motif: '#9FCAE0', floor: '#D8D2C8', ceiling: '#E8E8F0', signText: 'CITY MALL', counterOn: true, litter: false, picture: false, bulbs: true });
  const madM = person('madam', { height: 1.62 }), shambhu = person('shambhu', { height: 1.78 }), dukaan = person('dukaan', { height: 1.66 });
  ML.scene.add(madM.group, shambhu.group, dukaan.group);

  // ── 2D overlays (Latin text: Inter) ──
  const sticker = (text, x, y, sc = 1, { bg = '#FFFFFF', fg = INK, size = 72, rot = -0.04 } = {}) => {
    if (sc <= 0.01) return;
    ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc); ctx.font = `900 ${size}px ${F}`;
    const w = ctx.measureText(text).width + size * 1.0, h = size * 1.55;
    ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.beginPath(); ctx.roundRect(-w / 2 + 6, -h / 2 + 10, w, h, h * 0.4); ctx.fill();
    ctx.fillStyle = bg; ctx.strokeStyle = INK; ctx.lineWidth = 9; ctx.beginPath(); ctx.roundRect(-w / 2, -h / 2, w, h, h * 0.4); ctx.fill(); ctx.stroke();
    ctx.fillStyle = fg; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, 0, size * 0.04); ctx.restore();
  };
  const stamp = (text, x, y, sc, col = '#E0303A', rot = -0.2, size = 84) => { if (sc <= 0.01) return; ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(sc, sc); ctx.font = `900 ${size}px ${F}`;
    const w = ctx.measureText(text).width + 60; ctx.fillStyle = 'rgba(255,255,255,0.88)'; ctx.fillRect(-w / 2, -size * 0.75, w, size * 1.5); ctx.strokeStyle = col; ctx.lineWidth = 12; ctx.strokeRect(-w / 2, -size * 0.75, w, size * 1.5); ctx.fillStyle = col; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, 0, 4); ctx.restore(); };
  const bubble = (text, x, y, sc, tailX = 0) => { if (sc <= 0.01) return; ctx.save(); ctx.font = `900 56px ${F}`; const w = ctx.measureText(text).width + 70, h = 116; const cx = clamp(x, w / 2 + 24, 1056 - w / 2); tailX += x - cx; x = cx; ctx.translate(x, y); ctx.scale(sc, sc);
    ctx.fillStyle = '#FFFFFF'; ctx.strokeStyle = INK; ctx.lineWidth = 8; ctx.beginPath(); ctx.roundRect(-w / 2, -h / 2, w, h, 50); ctx.moveTo(tailX - 25, h / 2 - 2); ctx.lineTo(tailX + 10, h / 2 + 55); ctx.lineTo(tailX + 30, h / 2 - 2); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#FFFFFF'; ctx.fillRect(tailX - 22, h / 2 - 10, 50, 12); ctx.fillStyle = INK; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, 0, 3); ctx.restore(); };
  const arrowTo = (x0, y0, x1, y1, k) => { if (k <= 0) return; const x = lerp(x0, x1, k), y = lerp(y0, y1, k); ctx.save(); ctx.lineCap = 'round'; ctx.setLineDash([26, 22]); ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = 22; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x, y); ctx.stroke(); ctx.strokeStyle = '#E0303A'; ctx.lineWidth = 12; ctx.stroke(); ctx.restore(); };
  const rateCard = (rows, x, y, sc) => { if (sc <= 0.01) return; ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc); const w = 900, rh = 120, h = 140 + rows.length * rh;
    ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.fillRect(-w / 2 + 8, 12, w, h); ctx.fillStyle = '#FFF8E6'; ctx.strokeStyle = INK; ctx.lineWidth = 9; ctx.fillRect(-w / 2, 0, w, h); ctx.strokeRect(-w / 2, 0, w, h);
    ctx.fillStyle = '#B5372E'; ctx.fillRect(-w / 2, 0, w, 110); ctx.strokeRect(-w / 2, 0, w, 110); ctx.fillStyle = '#FFFFFF'; ctx.font = `900 62px ${F}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('THANA RATE CARD', 0, 58);
    rows.forEach(([a, b, k], i) => { if (k <= 0) return; ctx.globalAlpha = clamp(k * 2); const yy = 170 + i * rh; ctx.fillStyle = INK; ctx.font = `800 54px ${F}`; ctx.textAlign = 'left'; ctx.fillText(a, -w / 2 + 40, yy); ctx.textAlign = 'right'; ctx.fillStyle = '#B5372E'; ctx.font = `900 58px ${F}`; ctx.fillText(b, w / 2 - 40, yy); ctx.globalAlpha = 1; });
    ctx.restore(); };
  const lens = (x, y, r, sc, drawIn) => { if (sc <= 0.01) return; ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc); ctx.fillStyle = '#FFF4D6'; ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.fill(); ctx.save(); ctx.clip(); drawIn(); ctx.restore(); ctx.strokeStyle = INK; ctx.lineWidth = 16; ctx.beginPath(); ctx.arc(0, 0, r, 0, 7); ctx.stroke(); ctx.lineCap = 'round'; ctx.lineWidth = 34; ctx.beginPath(); ctx.moveTo(r * 0.72, r * 0.72); ctx.lineTo(r * 1.25, r * 1.25); ctx.stroke(); ctx.restore(); };
  const receipt = (x, y, sc) => { if (sc <= 0.01) return; ctx.save(); ctx.translate(x, y); ctx.rotate(-0.06); ctx.scale(sc, sc); ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.fillRect(-282, -172, 580, 360); ctx.fillStyle = '#FFFDF4'; ctx.strokeStyle = INK; ctx.lineWidth = 8; ctx.fillRect(-290, -180, 580, 360); ctx.strokeRect(-290, -180, 580, 360);
    ctx.fillStyle = INK; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.font = `900 40px ${F}`; ctx.fillText('"ESCORT POLICE TEAM", PATNA', 0, -120); ctx.font = `800 40px ${F}`; ctx.fillText('NAUKRI KI FEES', 0, -50); ctx.font = `900 110px ${F}`; ctx.fillStyle = '#B5372E'; ctx.fillText('₹90,000', 0, 60); ctx.font = `800 34px ${F}`; ctx.fillStyle = '#6A6A72'; ctx.fillText('received with thanks — Bhola', 0, 140); ctx.restore(); };

  // ── times (Devanagari words from the narration) ──
  const tPanch = Wd('पाँच', 0), tNakli0 = Wd('नकली', 0), tAsli0 = Wd('असली', 0);
  const tAath = Wd('आठ', 1), tPata = Wd('पता', 1);
  const tBanka = Wd('बांका', 2), tAnurag = Wd('अनुराग', 2), tHotel = Wd('होटल', 2), tBanG = Wd('बन', 2);
  const tVardi = Wd('वर्दी', 3), tTopi = Wd('टोपी', 3), tBilla = Wd('बिल्ला', 3), tPist = Wd('पिस्तौल', 3), tMadam3 = Wd('मैडम', 3), tSahab = Wd('साहब', 3);
  const tShik = Wd('शिकायत', 4), tSau = Wd('सौ', 4);
  const tGhar = Wd('सरकारी', 5), tPaise = Wd('पैसे', 5), tNauk = Wd('पुलिस', 5), tHaz = Wd('हज़ारों', 5);
  const tJama = Wd('जमा', 6), tEkBhi = Wd('एक', 6), tKam = Wd('भेजा', 6);
  const tMall = Wd('मॉल', 7), tJanch = Wd('जांच', 7);
  const tAsli8 = Wd('असली', 8), tDesi = Wd('देसी', 8);
  const tPucha = Wd('पूछा', 9), tPost = Wd('पोस्टिंग', 9), tPas = Wd('पसीने', 9);
  const tTwist = Wd('ट्विस्ट', 10), tNabbe = Wd('नब्बे', 10), tLaga = Wd('लगा', 10);
  const tThagi = Wd('ठगी', 11), tBhola = Wd('भोला', 11), tBaap = Wd('सबका', 11);
  const tBhejo = Wd('भेजो', 12), tSetting = Wd('सेटिंग', 12), tLike = Wd('लाइक', 12), tVarna = Wd('वरना', 12);

  const street = (people, from, to, at, k, look) => shoot(SR, people, from, to, at, k, look);
  const showS = (m, s, b, v) => { madS.group.visible = !!m; sahS.group.visible = !!s; bholaS.group.visible = !!b; vilS.group.visible = !!v; };
  const showT = (m, s, v, b) => { madT.group.visible = !!m; sahT.group.visible = !!s; vilT.group.visible = !!v; bholaT.group.visible = !!b; };

  // S0 · hook: a fake thana 500 m from the real one
  add({ id: 'S0', at: 0, note: 'street: fake thana near, real thana 500 m away', draw(lt, d, t, blit) {
    showS(1, 1, 0, 0); madS.at(-3.3, 0, -6.2); sahS.at(-3.6, 0, -9.4);
    madS.set({ mood: 'smug', armL: [10, 0], armR: [10, 0], holdR: KATTA, blink: blinkAt(t) }); sahS.set({ mood: 'proud', armL: [40, 120], armR: [40, 120], blink: blinkAt(t, 1) });
    street([madS, sahS], V3(1.5, 2.3, 9.0), V3(1.2, 2.5, 6.5), V3(-4.5, 3.2, -18), eio(seg(lt, 0, d)));
    blit();
    const [fx, fy] = proj(V3(-4.4, 5.0, -8)), [rx, ry] = proj(V3(-6.5, 10.5, -50));
    if (t >= tNakli0 - 0.1) sticker('NAKLI THANA', clamp(fx + 120, 260, 820), fy - 140, pop(t, tNakli0 - 0.1), { size: 70, bg: '#FF8A7A', rot: -0.06 });
    if (t >= tAsli0 - 0.1) sticker('ASLI THANA', clamp(rx, 260, 820), ry - 160, pop(t, tAsli0 - 0.1), { size: 62, bg: '#BFE4F7', rot: 0.05 });
    arrowTo(fx + 60, fy, rx - 20, ry, eo(seg(t, tPanch - 0.1, tPanch + 0.6)));
    if (t >= tPanch) sticker('500 m', (fx + rx) / 2 + 40, (fy + ry) / 2 - 40, pop(t, tPanch, 0.2), { size: 80, bg: '#FFE27A', rot: 0.04 });
  } });
  cue(tAsli0 - 0.1, 'pop'); cue(tPanch, 'zip', { gain: -6 }); cue(tNakli0 - 0.1, 'boing', { gain: -4 });
  // S1 · 8 months, nobody noticed
  add({ id: 'S1', at: cut(1), note: '8 months, nobody noticed', draw(lt, d, t, blit) {
    showS(1, 1, 0, 1); madS.at(-3.2, 0, -7.4); sahS.at(-3.3, 0, -8.8); vilS.at(-1.4, 0, -7.2);
    madS.set({ mood: 'happy', armL: [10, 0], armR: [130, 150], blink: blinkAt(t) }); sahS.set({ mood: 'smug', armL: [10, 0], armR: [10, 0], blink: blinkAt(t, 2) });
    vilS.set({ mood: 'happy', armR: [125, 150], armL: [10, 0], blink: blinkAt(t, 1), look: [-0.7, 0] });
    street([madS, sahS, vilS], V3(1.0, 1.7, -2.0), V3(0.6, 1.7, -3.0), V3(-2.6, 1.6, -8.0), eio(seg(lt, 0, d)));
    blit();
    const n = Math.max(1, Math.round(lerp(1, 8, eo(seg(t, tAath - 0.2, tAath + 1.2)))));
    sticker(`${n} MAHINE`, 540, 280, pop(t, tAath - 0.2), { size: 104, bg: '#FFE27A', rot: -0.04 });
    if (t >= tPata) stamp('KISI KO PATA NAHI', 540, 470, pop(t, tPata, 0.2), '#E0303A', 0.05, 66);
  } });
  for (let i = 0; i < 7; i++) cue(L(1) + 0.2 + i * 0.17, 'tock', { gain: -8 }); cue(tPata, 'stamp');
  // S2 · Anurag guest house: hotel room becomes thana
  add({ id: 'S2', at: cut(2), note: 'the guest house front: THANA board', draw(lt, d, t, blit) {
    showS(0, 0, 1, 0); bholaS.at(-3.3, 0, -6.6);
    bholaS.set({ mood: t >= tBanG ? 'laugh' : 'sly', armL: [10, 0], armR: t >= tBanG ? [140, 30] : [10, 0], blink: blinkAt(t), look: [-0.5, -0.3] });
    street([bholaS], V3(1.6, 1.6, -0.8), V3(0.8, 1.8, -2.4), V3(-4.2, 2.3, -8.0), eio(seg(lt, 0, d)));
    blit();
    sticker('BANKA, BIHAR', 540, 230, pop(t, tBanka - 0.05), { size: 70, bg: '#BFE4F7' });
    if (t >= tHotel) sticker('HOTEL KA KAMRA', 360, 1180, pop(t, tHotel), { size: 58, bg: '#FFFFFF', rot: -0.04 });
    if (t >= tBanG) sticker('= THANA', 700, 1290, pop(t, tBanG, 0.2), { size: 70, bg: '#FF8A7A', rot: 0.05 });
  } });
  cue(tBanka - 0.05, 'pop'); cue(tHotel, 'pop'); cue(tBanG, 'boing');
  // S3 · uniform, cap, badge, pistol — madam thanedar, sahab bade afsar
  add({ id: 'S3', at: cut(3), note: 'kit check: vardi topi billa pistol; ranks', draw(lt, d, t, blit) {
    showT(1, 1, 0, 0); madT.at(-0.45, 0, -3.0); sahT.at(0.55, 0, -3.2);
    madT.set({ mood: t >= tMadam3 ? 'proud' : 'smug', armL: [10, 0], armR: t >= tPist ? [40, 110] : [10, 0], holdR: t >= tPist ? KATTA : null, blink: blinkAt(t) });
    sahT.set({ mood: t >= tSahab ? 'proud' : 'neutral', armL: [40, 120], armR: [40, 120], blink: blinkAt(t, 1.3) });
    shoot(TH.scene, [madT, sahT], V3(0, 1.6, 1.2), V3(0, 1.6, 0.4), V3(0.05, 1.45, -3.1), eio(seg(lt, 0, d)));
    blit();
    [[tVardi, 'VARDI ✓', 250, 260], [tTopi, 'TOPI ✓', 820, 300], [tBilla, 'BILLA ✓', 250, 430], [tPist, 'PISTOL ✓', 800, 470]].forEach(([t0, s, x, y], i) => sticker(s, x, y, pop(t, t0 - 0.05), { size: 58, bg: ['#FFFFFF', '#FFE27A', '#BFE4F7', '#FF8A7A'][i], rot: (i % 2 ? 0.05 : -0.05) }));
    const [mx, my] = proj(V3(-0.45, 2.0, -3.0)), [sx, sy] = proj(V3(0.55, 2.1, -3.2));
    if (t >= tMadam3) sticker('THANEDAR', mx, my - 60, pop(t, tMadam3, 0.2), { size: 54, bg: '#9CE6A8', rot: -0.05 });
    if (t >= tSahab) sticker('BADE AFSAR', sx, sy - 40, pop(t, tSahab, 0.2), { size: 54, bg: '#E8E0FF', rot: 0.05 });
  } });
  [tVardi, tTopi, tBilla, tPist].forEach((t0) => cue(t0 - 0.05, 'pop')); cue(tMadam3, 'ding', { gain: -6 }); cue(tSahab, 'ding', { gain: -6 });
  // S4+S5 · the rate card
  add({ id: 'S4', at: cut(4), note: 'complaint counter + rate card', draw(lt, d, t, blit) {
    showT(1, 0, 1, 0); madT.at(-0.2, 0, -4.4); vilT.at(0.75, 0, -2.6);
    const late = t >= cut(5);
    madT.set({ mood: t >= tHaz ? 'laugh' : 'smug', armL: [60, 110], armR: [10, 0], holdL: late ? PROPS.cash(3) : FORM, talk: talk(t >= tShik - 0.1 && t < tSau + 0.6, t), blink: blinkAt(t), look: [0.5, 0] });
    vilT.set({ mood: t >= tHaz ? 'shock' : 'worried', armL: [10, 0], armR: [60, 90], holdR: t >= tPaise ? PROPS.cash(1) : null, sweat: t >= tHaz ? 1 : 0, blink: blinkAt(t, 2), look: [-0.6, 0] });
    shoot(TH.scene, [madT, vilT], V3(0.9, 1.75, 0.6), V3(0.6, 1.7, -0.1), V3(0.1, 1.3, -3.9), eio(seg(lt, 0, d)));
    blit();
    rateCard([['Shikayat', '₹100–500', seg(t, tSau - 0.1, tSau + 0.3)], ['Ghar ka form', '₹₹₹', seg(t, tPaise - 0.1, tPaise + 0.3)], ['Police naukri', 'HAZAARON', seg(t, tHaz - 0.1, tHaz + 0.3)]], 540, 150, pop(t, tShik - 0.1));
  } });
  cue(tShik - 0.1, 'whoosh'); cue(tSau, 'ding'); cue(tPaise, 'ding'); cue(tHaz, 'ding'); cue(tHaz + 0.3, 'boing', { gain: -6 });
  // S6 · 500+ forms, none sent on
  add({ id: 'S6', at: cut(6), note: '500+ forms piled up, 0 sent', draw(lt, d, t, blit) {
    showT(1, 1, 0, 0); madT.at(-0.55, 0, -4.4); sahT.at(1.0, 0, -4.2);
    const k = eo(seg(t, L(6), tJama + 0.8)); stack.scale.y = Math.max(0.02, k * 0.55); stack.position.y = 0.86 + k * 0.275;
    madT.set({ mood: 'smug', armL: [10, 0], armR: [10, 0], blink: blinkAt(t), look: [0.5, -0.3] });
    sahT.set({ mood: t >= tKam ? 'laugh' : 'sly', armL: [10, 0], armR: [10, 0], blink: blinkAt(t, 1), look: [-0.5, -0.3] });
    ctx.save(); ctx.translate(jolt(t, tKam), 0);
    shoot(TH.scene, [madT, sahT], V3(0.4, 1.9, -0.6), V3(0.4, 1.8, -1.3), V3(0.3, 1.2, -3.9), eio(seg(lt, 0, d)));
    blit(); ctx.restore();
    sticker(`FORMS: ${Math.round(lerp(0, 500, k))}+`, 540, 250, pop(t, L(6)), { size: 84, bg: '#FFFFFF' });
    if (t >= tEkBhi - 0.1) sticker('AAGE BHEJE: 0', 540, 420, pop(t, tEkBhi - 0.1), { size: 76, bg: '#FF8A7A', rot: 0.04 });
    if (t >= tKam) stamp('ZERO!', 540, 610, pop(t, tKam, 0.15), '#E0303A', -0.1, 96);
    stack.scale.y = stack.scale.y; } });
  cue(L(6), 'pop'); for (let i = 0; i < 8; i++) cue(L(6) + 0.2 + i * 0.12, 'plop', { gain: -12 }); cue(tEkBhi - 0.1, 'sputter', { gain: -6 }); cue(tKam, 'stamp');
  // S7 · madam goes to inspect shops at a mall
  add({ id: 'S7', at: cut(7), note: 'madam "inspects" the mall', draw(lt, d, t, blit) {
    shambhu.group.visible = false; madM.group.visible = dukaan.group.visible = true;
    const wk = seg(t, L(7), tJanch + 0.4); madM.at(lerp(-2.6, -0.5, eo(wk)), 0, -3.4); dukaan.at(0.8, 0, -3.8);
    madM.set({ mood: 'smug', legs: wk > 0 && wk < 1 ? 'walk' : 'stand', phase: t * 9, armL: [60, 100], holdL: FORM, armR: [10, 0], holdR: KATTA, blink: blinkAt(t), look: [0.6, 0] });
    dukaan.set({ mood: t >= tJanch ? 'worried' : 'neutral', armL: [10, 0], armR: [10, 0], sweat: t >= tJanch ? 1 : 0, look: [-0.6, 0], blink: blinkAt(t, 2) });
    shoot(ML.scene, [madM, dukaan], V3(0.2, 1.6, 1.2), V3(0.1, 1.6, 0.4), V3(0, 1.35, -3.6), eio(seg(lt, 0, d)));
    blit();
    if (t >= tMall - 0.1) sticker('CITY MALL', 540, 250, pop(t, tMall - 0.1), { size: 80, bg: '#BFE4F7' });
    if (t >= tJanch) sticker('"SITE INSPECTION"', 540, 420, pop(t, tJanch, 0.2), { size: 62, bg: '#FFE27A', rot: -0.04 });
  } });
  cue(tMall - 0.1, 'pop'); cue(tJanch, 'pop');
  // S8 · the real thanedar spots a desi katta
  add({ id: 'S8', at: cut(8), note: 'real SHO notices the country-made pistol', draw(lt, d, t, blit) {
    shambhu.group.visible = madM.group.visible = true; dukaan.group.visible = false;
    const wk = seg(t, L(8) - 0.1, L(8) + 0.9); shambhu.at(lerp(2.8, 0.7, eo(wk)), 0, -3.3); madM.at(-0.45, 0, -3.4);
    shambhu.set({ mood: t >= tDesi ? 'angry' : 'sly', legs: wk < 1 ? 'walk' : 'stand', phase: t * 9, armL: [10, 0], armR: [10, 0], look: [-0.6, 0.5], blink: blinkAt(t) });
    madM.set({ mood: 'smug', armL: [10, 0], armR: [20, 40], holdR: KATTA, blink: blinkAt(t, 1), look: [0.5, 0] });
    shoot(ML.scene, [shambhu, madM], V3(0.1, 1.55, 1.0), V3(0.1, 1.5, 0.2), V3(0.1, 1.3, -3.4), eio(seg(lt, 0, d)));
    blit();
    if (t >= tAsli8) sticker('ASLI THANEDAR', 760, 300, pop(t, tAsli8), { size: 60, bg: '#9CE6A8', rot: 0.05 });
    const [kx, ky] = proj(V3(-0.32, 0.9, -3.4));
    lens(330, 760, 190, pop(t, tDesi - 0.3, 0.3), () => { ctx.save(); ctx.scale(2.6, 2.6); ctx.translate(-37, 17); KATTA(ctx, 0, 0); ctx.restore(); });
    if (t >= tDesi - 0.3) { ctx.save(); ctx.strokeStyle = 'rgba(255,255,255,0.7)'; ctx.lineWidth = 6; ctx.setLineDash([12, 12]); ctx.beginPath(); ctx.moveTo(kx, ky); ctx.lineTo(420, 900); ctx.stroke(); ctx.restore(); }
    if (t >= tDesi) stamp('DESI KATTA!', 600, 1030, pop(t, tDesi, 0.15), '#E0303A', -0.08, 90);
  } });
  cue(L(8), 'whoosh'); cue(tDesi - 0.3, 'sparkle', { dur: 0.6, gain: -8 }); cue(tDesi, 'stamp');
  // S9 · "posting kahan hai?" — sweat
  add({ id: 'S9', at: cut(9), note: 'where are you posted? she sweats', draw(lt, d, t, blit) {
    shambhu.group.visible = madM.group.visible = true; dukaan.group.visible = false;
    shambhu.at(0.55, 0, -3.3); madM.at(-0.45, 0, -3.4);
    const sw = t >= tPas - 0.2;
    shambhu.set({ mood: 'sly', armL: [10, 0], armR: [70, 120], talk: talk(t >= tPucha && t < tPas - 0.3, t), look: [-0.6, 0], blink: blinkAt(t) });
    madM.set({ mood: sw ? 'worried' : 'neutral', armL: [10, 0], armR: [10, 0], sweat: sw ? 1 : 0, look: [0.5, 0], blink: blinkAt(t, 1) });
    ctx.save(); ctx.translate(jolt(t, tPas), 0);
    shoot(ML.scene, [shambhu, madM], V3(-0.3, 1.65, 0.3), V3(-0.4, 1.65, -0.5), V3(-0.2, 1.55, -3.4), eio(seg(lt, 0, d)));
    blit(); ctx.restore();
    const [bx, by] = proj(V3(0.55, 2.1, -3.3));
    if (t < tPas - 0.2) bubble('Posting kahan hai?', bx - 80, by - 110, pop(t, tPucha), 60);
    if (sw) { sticker('GULP...', 300, 330, pop(t, tPas - 0.2, 0.2), { size: 80, bg: '#BFE4F7', rot: -0.06 });
      for (let i = 0; i < 5; i++) { const k = ((t * 1.6 + i * 0.2) % 1); ctx.fillStyle = '#7FC8F2'; ctx.strokeStyle = INK; ctx.lineWidth = 5; const [hx, hy] = proj(V3(-0.45, 1.5, -3.4)); const x = hx + (i - 2) * 70, y = hy - 120 + k * 260; ctx.globalAlpha = 1 - k; ctx.beginPath(); ctx.moveTo(x, y - 30); ctx.quadraticCurveTo(x + 22, y + 6, x, y + 16); ctx.quadraticCurveTo(x - 22, y + 6, x, y - 30); ctx.fill(); ctx.stroke(); ctx.globalAlpha = 1; } }
  } });
  cue(tPucha, 'pop'); cue(tPas - 0.2, 'gulp'); cue(tPas, 'boing', { gain: -6 });
  // S10 · twist: madam herself paid ₹90,000 for the "job"
  add({ id: 'S10', at: cut(10), note: 'twist: she paid 90k bribe, thought it was real police', draw(lt, d, t, blit) {
    shambhu.group.visible = madM.group.visible = true; dukaan.group.visible = false;
    shambhu.at(0.7, 0, -3.4); madM.at(-0.2, 0, -3.2);
    madM.set({ mood: t >= tLaga ? 'sad' : 'shock', armL: [10, 0], armR: [10, 0], tears: t >= tLaga ? 1 : 0, look: [0, 0], blink: blinkAt(t) });
    shambhu.set({ mood: t >= tLaga ? 'shock' : 'neutral', armL: [10, 0], armR: [10, 0], look: [-0.6, 0], blink: blinkAt(t, 1) });
    shoot(ML.scene, [shambhu, madM], V3(-0.1, 1.6, 0.4), V3(-0.1, 1.6, -0.4), V3(0.1, 1.5, -3.3), eio(seg(lt, 0, d)));
    blit();
    sticker('ASLI TWIST', 540, 200, pop(t, tTwist - 0.1), { size: 86, bg: '#E8E0FF', rot: -0.03 });
    receipt(540, 520, pop(t, tNabbe - 0.15, 0.3));
    const [mx, my] = proj(V3(-0.2, 2.0, -3.2)); if (t >= tLaga) bubble('Main toh asli police hoon!', mx + 60, my - 60, pop(t, tLaga), -40);
  } });
  cue(tTwist - 0.1, 'whoosh'); cue(tNabbe - 0.15, 'slam', { gain: -4 }); cue(tLaga, 'sputter', { gain: -6 });
  // S11 · fake police got conned too — Bhola sabka baap
  add({ id: 'S11', at: cut(11), note: 'mastermind Bhola counts cash', draw(lt, d, t, blit) {
    showT(0, 0, 0, 1); bholaT.at(0.1, 0, -3.5); stack.scale.y = 0.55; stack.position.y = 1.135;
    bholaT.set({ mood: t >= tBaap ? 'laugh' : 'sly', holdL: PROPS.stack, holdR: PROPS.cash(4), armL: [50, 90], armR: [50, 90], bob: t >= tBaap ? -14 * Math.abs(Math.sin(t * 8)) : 0, blink: blinkAt(t) });
    ctx.save(); ctx.translate(jolt(t, tBaap), 0);
    shoot(TH.scene, [bholaT], V3(0.1, 1.55, 0.2), V3(0.1, 1.6, -0.6), V3(0.1, 1.5, -3.5), eio(seg(lt, 0, d)));
    blit(); ctx.restore();
    sticker('NAKLI POLICE BHI THAGI GAYI', 540, 230, pop(t, tThagi - 0.2), { size: 52, bg: '#FFFFFF' });
    if (t >= tBhola) sticker('MASTERMIND: BHOLA', 540, 400, pop(t, tBhola), { size: 66, bg: '#FFE27A', rot: 0.03 });
    if (t >= tBaap) stamp('SABKA BAAP', 540, 600, pop(t, tBaap, 0.2), '#E0303A', -0.08, 100);
  } });
  cue(tThagi - 0.2, 'pop'); cue(tBhola, 'pop'); cue(tBaap, 'stamp'); cue(tBaap + 0.4, 'boing');
  // S12 · CTA: send to the "meri upar tak setting hai" friend + like
  add({ id: 'S12', at: cut(12), note: 'CTA: send + like', draw(lt, d, t, blit) {
    showS(1, 1, 1, 0); bholaS.at(-2.4, 0, -6.6); madS.at(-3.2, 0, -7.6); sahS.at(-1.6, 0, -7.8);
    bholaS.set({ mood: 'laugh', armL: [150, 30], armR: [150, 30], blink: blinkAt(t) });
    madS.set({ mood: 'smug', armL: [10, 0], armR: [125, 150], blink: blinkAt(t, 1) }); sahS.set({ mood: 'smug', armL: [125, 150], armR: [10, 0], blink: blinkAt(t, 2) });
    street([bholaS, madS, sahS], V3(0.6, 1.7, -0.6), V3(0.2, 1.7, -2.0), V3(-2.4, 1.9, -7.4), eio(seg(lt, 0, d)));
    blit();
    if (t >= tBhejo - 0.1) sticker('DOST KO BHEJO', 540, 250, pop(t, tBhejo - 0.1), { size: 84, bg: '#9CE6A8', rot: -0.04 });
    if (t >= tSetting - 0.1) sticker('"UPAR TAK SETTING HAI"', 540, 410, pop(t, tSetting - 0.1), { size: 54, bg: '#FFFFFF', rot: 0.03 });
    if (t >= tLike - 0.1) sticker('LIKE KARO ♥', 540, 600, pop(t, tLike - 0.1, 0.2), { size: 92, bg: '#FF6FB0', fg: '#FFFFFF', rot: -0.05 });
    if (t >= tVarna) stamp('WARNA NAKLI THANA!', 540, 790, pop(t, tVarna, 0.2), '#E0303A', 0.05, 62);
  } });
  cue(tBhejo - 0.1, 'pop'); cue(tSetting - 0.1, 'pop'); cue(tLike - 0.1, 'levelup', { gain: -6 }); cue(tVarna, 'stamp');
  return { shots: S, cues: CUES };
}
