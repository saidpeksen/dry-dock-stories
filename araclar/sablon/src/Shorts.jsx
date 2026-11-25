// Dry Dock Stories – Shorts şablonu (Remotion).
// Sabit stil: soğuk renk ayarı, bölümler arası kısa geçiş, sol üstte filigran, alt üçte birde kelime kelime
// vurgulu altyazı. Görsel blokları yavaş yakınlaşır/uzaklaşır; harita blokları araclar/harita bileşeniyle çizilir.
// İsteğe bağlı (props'ta varsa): ilk kare başlığı (headline) ve sağ üst köşe etiketi (label). Yoksa hiçbir şey çizilmez.
import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, Easing, Img, Sequence, continueRender, cancelRender, delayRender, interpolate,
  staticFile, useCurrentFrame} from 'remotion';
import {MapScene} from '../../harita/src/MapScene.jsx';

export const W = 1080, H = 1920;
const GECIS = 8;                 // bölümler arası geçiş (kare)
const ALTYAZI_Y = 1290;          // altyazı bloğunun ortası: Shorts arayüzünün (alt yazı/düğmeler) üstünde
const VURGU = '#F2B544';         // konuşulan kelime (harita rotasıyla aynı renk)
const YAZI = 'DDS Montserrat';

// Yazı tipi (OFL, public/fonts) yüklenmeden kare alınmaz.
const yaziBekle = delayRender('Yazı tipi yükleniyor');
const yaziHazir = Promise.all([
  new FontFace(YAZI, `url(${staticFile('fonts/Montserrat-ExtraBold.woff2')})`, {weight: '800'}).load(),
  new FontFace(YAZI, `url(${staticFile('fonts/Montserrat-SemiBold.woff2')})`, {weight: '600'}).load(),
]).then((fs) => { fs.forEach((f) => document.fonts.add(f)); continueRender(yaziBekle); });
yaziHazir.catch((e) => cancelRender(e));

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

// Köşe etiketi: sağ üstte, filigranla aynı hizada küçük yazı (video boyunca).
const Etiket = ({metin}) => (
  <div style={{position: 'absolute', right: 56, top: 92, height: 34, display: 'flex', alignItems: 'center', opacity: 0.78,
    fontFamily: YAZI, fontWeight: 600, fontSize: 24, letterSpacing: 1, color: '#ffffff', whiteSpace: 'nowrap',
    textShadow: '0 2px 6px rgba(0,0,0,0.6)'}}>{metin}</div>
);

// İlk kare başlığı: videonun ilk karesinden itibaren kısa süre görünen büyük yazı (2–4 kelime).
// Kelimeler en çok üç satıra bölünür; yazının gerçek genişliği ölçülür ve BASLIK_EN'e sığan en büyük boyut seçilir.
// Blok, filigran ve etiket bandının altında (BASLIK_UST), altyazı bandının üstünde (BASLIK_ALT) kalır.
const BASLIK_EN = 940, BASLIK_UST = 190, BASLIK_ALT = 1150, BASLIK_Y = 480;
const BASLIK_BOYUT = 150, BASLIK_YETER = 120, BASLIK_SATIR = 1.06;

const emGenislik = (metin) => {   // 1 em'e göre genişlik; yazı tipi yüklendikten sonra çağrılır
  const s = document.createElement('span');
  s.style.cssText = `position:absolute;left:-9999px;top:0;visibility:hidden;white-space:nowrap;font-family:"${YAZI}";font-weight:800;font-size:200px`;
  s.textContent = metin;
  document.body.appendChild(s);
  const w = s.getBoundingClientRect().width / 200;
  s.remove();
  return w;
};

const bolmeler = (kelimeler, n) => {   // kelimeleri sırayı bozmadan n satıra bölmenin bütün yolları
  if (n === 1) return [[kelimeler.join(' ')]];
  const out = [];
  for (let i = 1; i <= kelimeler.length - (n - 1); i++) {
    for (const kalan of bolmeler(kelimeler.slice(i), n - 1)) out.push([kelimeler.slice(0, i).join(' '), ...kalan]);
  }
  return out;
};

const baslikYerlesimi = (metin) => {   // en az satırla BASLIK_YETER'e ulaşan bölme; ulaşılamıyorsa en büyük yazı
  const kelimeler = metin.split(' ').filter(Boolean);
  let secim = null;
  for (let n = 1; n <= Math.min(3, kelimeler.length); n++) {
    for (const satirlar of bolmeler(kelimeler, n)) {
      const enler = satirlar.map(emGenislik);
      const boyut = Math.min(BASLIK_BOYUT, BASLIK_EN / Math.max(...enler));
      const denge = Math.min(...enler) / Math.max(...enler);
      if (!secim || boyut > secim.boyut + 0.5 || (secim.satirlar.length === n && Math.abs(boyut - secim.boyut) <= 0.5 && denge > secim.denge)) {
        secim = {satirlar, boyut, denge};
      }
    }
    if (secim.boyut >= BASLIK_YETER) break;
  }
  return secim;
};

const Baslik = ({text, frames = 45, y}) => {
  const f = useCurrentFrame();
  const [bekle] = useState(() => delayRender('Başlık ölçülüyor'));
  const [d, setD] = useState(null);
  useEffect(() => {
    let iptal = false;
    yaziHazir.then(() => { if (!iptal) setD(baslikYerlesimi(text)); }).catch((e) => cancelRender(e));
    return () => { iptal = true; };
  }, [text]);
  useEffect(() => { if (d) continueRender(bekle); }, [d, bekle]);
  useEffect(() => () => continueRender(bekle), [bekle]);   // bileşen erken kalkarsa bekleme açık kalmasın
  if (!d) return null;
  const yukseklik = d.satirlar.length * d.boyut * BASLIK_SATIR;
  const orta = Math.max(BASLIK_UST + yukseklik / 2, Math.min(BASLIK_ALT - yukseklik / 2, typeof y === 'number' ? y : BASLIK_Y));
  const op = interpolate(f, [frames - 7, frames - 1], [1, 0], clamp);          // ilk kareden itibaren tam görünür
  const sc = interpolate(f, [0, 6], [1.05, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const cizgi = Math.round(d.boyut * 0.1);
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: orta, textAlign: 'center', opacity: op,
      transform: `translateY(-50%) scale(${sc})`}}>
      <div style={{position: 'absolute', left: 0, right: 0, top: -130, bottom: -130,
        background: 'radial-gradient(ellipse 62% 50% at 50% 50%, rgba(3,8,14,0.6) 0%, rgba(3,8,14,0.38) 45%, rgba(3,8,14,0) 100%)'}} />
      {d.satirlar.map((s, i) => (
        <div key={i} style={{position: 'relative', fontFamily: YAZI, fontWeight: 800, fontSize: d.boyut, lineHeight: BASLIK_SATIR,
          whiteSpace: 'nowrap', color: '#ffffff', WebkitTextStroke: `${cizgi}px #060b11`, paintOrder: 'stroke fill',
          textShadow: '0 10px 26px rgba(0,0,0,0.6)'}}>{s}</div>
      ))}
    </div>
  );
};

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

export const Shorts = ({blocks = [], chunks = [], audio, headline, label}) => (
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
    {label ? <Etiket metin={label} /> : null}
    <Altyazi chunks={chunks} />
    {headline && headline.text ? (
      <Sequence from={0} durationInFrames={Math.max(1, headline.frames || 45)}>
        <Baslik text={headline.text} frames={Math.max(1, headline.frames || 45)} y={headline.y} />
      </Sequence>
    ) : null}
    {audio ? <Audio src={staticFile(audio)} /> : null}
  </AbsoluteFill>
);
