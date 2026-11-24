// Dry Dock Stories – Shorts şablonu (Remotion).
// Sabit stil: soğuk renk ayarı, bölümler arası kısa geçiş, sol üstte filigran, alt üçte birde kelime kelime
// vurgulu altyazı. Görsel blokları yavaş yakınlaşır/uzaklaşır; harita blokları araclar/harita bileşeniyle çizilir.
import React from 'react';
import {AbsoluteFill, Audio, Img, Sequence, continueRender, cancelRender, delayRender, interpolate,
  staticFile, useCurrentFrame} from 'remotion';
import {MapScene} from '../../harita/src/MapScene.jsx';

export const W = 1080, H = 1920;
const GECIS = 8;                 // bölümler arası geçiş (kare)
const ALTYAZI_Y = 1290;          // altyazı bloğunun ortası: Shorts arayüzünün (alt yazı/düğmeler) üstünde
const VURGU = '#F2B544';         // konuşulan kelime (harita rotasıyla aynı renk)
const YAZI = 'DDS Montserrat';

// Yazı tipi (OFL, public/fonts) yüklenmeden kare alınmaz.
const yaziBekle = delayRender('Yazı tipi yükleniyor');
Promise.all([
  new FontFace(YAZI, `url(${staticFile('fonts/Montserrat-ExtraBold.woff2')})`, {weight: '800'}).load(),
  new FontFace(YAZI, `url(${staticFile('fonts/Montserrat-SemiBold.woff2')})`, {weight: '600'}).load(),
]).then((fs) => { fs.forEach((f) => document.fonts.add(f)); continueRender(yaziBekle); })
  .catch((e) => cancelRender(e));

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'};

const Gorsel = ({src, frames, zoomIn}) => {
  const f = useCurrentFrame();
  const p = Math.min(1, f / Math.max(1, frames - 1));
  const s = zoomIn ? 1 + 0.12 * p : 1.12 - 0.12 * p;
  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: '#05090e'}}>
      <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover', transform: `scale(${s})`}} />
    </AbsoluteFill>
  );
};

// Bölüm girişi: kısa saydamlık geçişi ve hafif yaklaşma.
const Gecis = ({ilk, children}) => {
  const f = useCurrentFrame();
  const o = ilk ? 1 : interpolate(f, [0, GECIS], [0, 1], clamp);
  const s = ilk ? 1 : interpolate(f, [0, GECIS], [1.035, 1], clamp);
  return <AbsoluteFill style={{opacity: o, transform: `scale(${s})`}}>{children}</AbsoluteFill>;
};

// Renk ayarı ve okunurluk katmanı (her karede aynı).
const Katman = () => (
  <AbsoluteFill style={{pointerEvents: 'none'}}>
    <AbsoluteFill style={{backgroundColor: '#1d3a52', mixBlendMode: 'soft-light', opacity: 0.35}} />
    <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(3,8,14,0.55) 0%, rgba(3,8,14,0) 14%, rgba(3,8,14,0) 52%, rgba(3,8,14,0.62) 78%, rgba(3,8,14,0.78) 100%)'}} />
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 42%, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)'}} />
  </AbsoluteFill>
);

const Filigran = () => (
  <div style={{position: 'absolute', left: 56, top: 92, display: 'flex', alignItems: 'center', gap: 14, opacity: 0.78}}>
    <div style={{width: 6, height: 34, backgroundColor: VURGU, borderRadius: 3}} />
    <div style={{fontFamily: YAZI, fontWeight: 600, fontSize: 26, letterSpacing: 6, color: '#ffffff',
      textShadow: '0 2px 6px rgba(0,0,0,0.6)'}}>DRY DOCK STORIES</div>
  </div>
);

const kontur = ['-3px -3px', '3px -3px', '-3px 3px', '3px 3px', '0 -3px', '0 3px', '-3px 0', '3px 0']
  .map((o) => `${o} 0 #060b11`).join(', ') + ', 0 6px 14px rgba(0,0,0,0.55)';

const Altyazi = ({chunks}) => {
  const f = useCurrentFrame();
  const c = chunks.find((x) => f >= x.start && f < x.end);
  if (!c) return null;
  const l = f - c.start;
  const op = interpolate(l, [0, 3], [0, 1], clamp);
  const sc = interpolate(l, [0, 4], [0.94, 1], clamp);
  return (
    <div style={{position: 'absolute', left: 110, right: 110, top: ALTYAZI_Y, textAlign: 'center',
      transform: `translateY(-50%) scale(${sc})`, opacity: op}}>
      {c.lines.map((line, li) => (
        <div key={li} style={{lineHeight: 1.18, whiteSpace: 'nowrap'}}>
          {line.map((w, wi) => {
            const on = f >= w.s && f < w.e;
            return (
              <span key={wi} style={{display: 'inline-block', margin: '0 13px', fontFamily: YAZI, fontWeight: 800,
                fontSize: 74, color: on ? VURGU : '#ffffff', textShadow: kontur,
                transform: on ? 'scale(1.06)' : 'none'}}>{w.t}</span>
            );
          })}
        </div>
      ))}
    </div>
  );
};

export const Shorts = ({blocks = [], chunks = [], audio}) => (
  <AbsoluteFill style={{backgroundColor: '#05090e'}}>
    {blocks.map((b, i) => {
      const len = Math.max(1, b.end - b.start);
      const dur = len + (i < blocks.length - 1 ? GECIS : 0);
      return (
        <Sequence key={i} from={b.start} durationInFrames={dur}>
          <Gecis ilk={i === 0}>
            {b.kind === 'map'
              ? <MapScene {...b.map} frames={len} />
              : <Gorsel src={b.src} frames={len} zoomIn={i % 2 === 0} />}
          </Gecis>
        </Sequence>
      );
    })}
    <Katman />
    <Filigran />
    <Altyazi chunks={chunks} />
    {audio ? <Audio src={staticFile(audio)} /> : null}
  </AbsoluteFill>
);
