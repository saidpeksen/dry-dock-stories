// Dry Dock Stories – uzun video şablonu (Remotion), yatay 1920×1080.
// Shorts şablonuyla aynı dil: soğuk renk ayarı, sol üstte filigran, sağ üstte köşe etiketi, konuşulan kelimesi
// vurgulu altyazı. Uzun videoya özgü parçalar: bölüm kartı, seri kartı, "tersaneden bakınca" şeridi, sayı kartı,
// bitiş kartı. Bu dosya Shorts şablonundan bağımsızdır (ayrı giriş noktası: src/uzun/index.jsx); Shorts çıktısını
// değiştirmez. Girdi biçimi: araclar/sablon/UZUN.md.
import React from 'react';
import {AbsoluteFill, Audio, Easing, Img, Sequence, continueRender, cancelRender, delayRender, interpolate,
  staticFile, useCurrentFrame} from 'remotion';

export const W = 1920, H = 1080;
const GECIS = 12;                // bloklar arası geçiş (kare)
const ALTYAZI_Y = 930;           // altyazı bloğunun ortası (alt üçte bir)
const VURGU = '#F2B544';         // konuşulan kelime, çizgiler, "tersaneden bakınca" şeridi
const KOYU = '#060b11';
const YAZI = 'DDS Montserrat';
const KENAR = 72;                // filigran ve etiketin kenar boşluğu

// Yazı tipi (OFL, public/fonts) yüklenmeden kare alınmaz.
const yaziBekle = delayRender('Yazı tipi yükleniyor');
Promise.all([
  new FontFace(YAZI, `url(${staticFile('fonts/Montserrat-ExtraBold.woff2')})`, {weight: '800'}).load(),
  new FontFace(YAZI, `url(${staticFile('fonts/Montserrat-SemiBold.woff2')})`, {weight: '600'}).load(),
]).then((fs) => { fs.forEach((f) => document.fonts.add(f)); continueRender(yaziBekle); })
  .catch((e) => cancelRender(e));

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'};
const yumusak = {...clamp, easing: Easing.inOut(Easing.cubic)};
const golge = '0 3px 10px rgba(0,0,0,0.65)';

// Görsel: yavaş yakınlaşma, uzaklaşma ya da yana kayma. Uzun bloklarda hız düşük kalsın diye toplam hareket küçüktür.
const Gorsel = ({src, frames, move}) => {
  const f = useCurrentFrame();
  const p = Math.min(1, f / Math.max(1, frames - 1));
  let s = 1.1, x = 0;
  if (move === 'in') s = 1 + 0.1 * p;
  else if (move === 'out') s = 1.1 - 0.1 * p;
  else if (move === 'left') x = 2.2 - 4.4 * p;      // yüzde
  else x = -2.2 + 4.4 * p;
  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: '#05090e'}}>
      <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover',
        transform: `translateX(${x}%) scale(${s})`}} />
    </AbsoluteFill>
  );
};

const Gecis = ({ilk, children}) => {
  const f = useCurrentFrame();
  const o = ilk ? 1 : interpolate(f, [0, GECIS], [0, 1], clamp);
  return <AbsoluteFill style={{opacity: o}}>{children}</AbsoluteFill>;
};

// Renk ayarı ve okunurluk katmanı (her karede aynı).
const Katman = () => (
  <AbsoluteFill style={{pointerEvents: 'none'}}>
    <AbsoluteFill style={{backgroundColor: '#1d3a52', mixBlendMode: 'soft-light', opacity: 0.35}} />
    <AbsoluteFill style={{background: 'linear-gradient(180deg, rgba(3,8,14,0.5) 0%, rgba(3,8,14,0) 16%, rgba(3,8,14,0) 62%, rgba(3,8,14,0.6) 84%, rgba(3,8,14,0.8) 100%)'}} />
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 60%, rgba(0,0,0,0.4) 100%)'}} />
  </AbsoluteFill>
);

const Filigran = () => (
  <div style={{position: 'absolute', left: KENAR, top: 56, display: 'flex', alignItems: 'center', gap: 14, opacity: 0.78}}>
    <div style={{width: 6, height: 32, backgroundColor: VURGU, borderRadius: 3}} />
    <div style={{fontFamily: YAZI, fontWeight: 600, fontSize: 24, letterSpacing: 6, color: '#ffffff',
      textShadow: golge}}>DRY DOCK STORIES</div>
  </div>
);

const Etiket = ({metin}) => (
  <div style={{position: 'absolute', right: KENAR, top: 56, height: 32, display: 'flex', alignItems: 'center', opacity: 0.78,
    fontFamily: YAZI, fontWeight: 600, fontSize: 22, letterSpacing: 1, color: '#ffffff', whiteSpace: 'nowrap',
    textShadow: golge}}>{metin}</div>
);

// Kartların ortak giriş ve çıkışı: kısa saydamlık geçişi; çizgi soldan açılır.
const kartGorunum = (f, frames) => ({
  op: Math.min(interpolate(f, [0, 8], [0, 1], clamp), interpolate(f, [frames - 12, frames - 1], [1, 0], clamp)),
  cizgi: interpolate(f, [4, 26], [0, 1], yumusak),
  kay: interpolate(f, [0, 16], [26, 0], {...clamp, easing: Easing.out(Easing.cubic)}),
});

const Karartma = ({op, guc = 0.62}) => (
  <AbsoluteFill style={{backgroundColor: `rgba(3,8,14,${guc})`, opacity: op}} />
);

// Bölüm kartı: bölümün başında, ilk görselin üstünde; solda küçük sıra yazısı ve bölüm başlığı.
const BolumKarti = ({kicker, title, frames}) => {
  const f = useCurrentFrame();
  const g = kartGorunum(f, frames);
  return (
    <AbsoluteFill>
      <Karartma op={g.op} />
      <div style={{position: 'absolute', left: 170, right: 300, top: '50%', transform: `translateY(-50%) translateY(${g.kay}px)`,
        opacity: g.op}}>
        {kicker ? <div style={{fontFamily: YAZI, fontWeight: 600, fontSize: 30, letterSpacing: 8, color: VURGU,
          textShadow: golge, marginBottom: 22}}>{kicker}</div> : null}
        <div style={{fontFamily: YAZI, fontWeight: 800, fontSize: 86, lineHeight: 1.08, color: '#ffffff',
          textShadow: '0 8px 24px rgba(0,0,0,0.6)'}}>{title}</div>
        <div style={{width: 220 * g.cizgi, height: 7, backgroundColor: VURGU, borderRadius: 4, marginTop: 34}} />
      </div>
    </AbsoluteFill>
  );
};

// Seri kartı: serinin adı ortada; üstünde küçük seri yazısı, altında bu videonun sorusu.
const SeriKarti = ({tag, name, title, frames}) => {
  const f = useCurrentFrame();
  const g = kartGorunum(f, frames);
  return (
    <AbsoluteFill>
      <Karartma op={g.op} guc={0.72} />
      <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', opacity: g.op,
        transform: `translateY(${g.kay * 0.6}px)`}}>
        {tag ? <div style={{fontFamily: YAZI, fontWeight: 600, fontSize: 28, letterSpacing: 9, color: '#ffffff',
          opacity: 0.85, textShadow: golge}}>{tag}</div> : null}
        <div style={{display: 'flex', alignItems: 'center', gap: 34, marginTop: 26}}>
          <div style={{width: 150 * g.cizgi, height: 6, backgroundColor: VURGU, borderRadius: 3}} />
          <div style={{fontFamily: YAZI, fontWeight: 800, fontSize: 124, letterSpacing: 3, color: '#ffffff', whiteSpace: 'nowrap',
            textShadow: '0 10px 28px rgba(0,0,0,0.6)'}}>{name}</div>
          <div style={{width: 150 * g.cizgi, height: 6, backgroundColor: VURGU, borderRadius: 3}} />
        </div>
        {title ? <div style={{fontFamily: YAZI, fontWeight: 600, fontSize: 42, color: VURGU, marginTop: 30, maxWidth: 1400,
          textAlign: 'center', lineHeight: 1.2, textShadow: golge}}>{title}</div> : null}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// Bitiş kartı: sol yarıda sıradaki soru; sağ yarı YouTube bitiş ekranı öğeleri için boş kalır.
const BitisKarti = ({kicker, title, frames}) => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 12], [0, 1], clamp);
  const cizgi = interpolate(f, [6, 30], [0, 1], yumusak);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{background: 'linear-gradient(90deg, rgba(3,8,14,0.86) 0%, rgba(3,8,14,0.78) 46%, rgba(3,8,14,0.5) 100%)', opacity: op}} />
      <div style={{position: 'absolute', left: 150, width: 760, top: '46%', transform: 'translateY(-50%)', opacity: op}}>
        {kicker ? <div style={{fontFamily: YAZI, fontWeight: 600, fontSize: 28, letterSpacing: 8, color: VURGU,
          marginBottom: 20}}>{kicker}</div> : null}
        <div style={{fontFamily: YAZI, fontWeight: 800, fontSize: 64, lineHeight: 1.12, color: '#ffffff',
          textShadow: '0 8px 24px rgba(0,0,0,0.6)'}}>{title}</div>
        <div style={{width: 180 * cizgi, height: 6, backgroundColor: VURGU, borderRadius: 3, marginTop: 30}} />
      </div>
    </AbsoluteFill>
  );
};

// "Tersaneden bakınca" şeridi: uzman notu bölümü boyunca solda renkli dikey şerit ve üstte etiket.
const NotSeridi = ({label, by, frames}) => {
  const f = useCurrentFrame();
  const op = Math.min(interpolate(f, [0, 12], [0, 1], clamp), interpolate(f, [frames - 12, frames - 1], [1, 0], clamp));
  const boy = interpolate(f, [0, 20], [0, 1], yumusak);
  return (
    <AbsoluteFill style={{opacity: op}}>
      <AbsoluteFill style={{backgroundColor: 'rgba(24,16,4,0.22)'}} />
      <div style={{position: 'absolute', left: 0, top: 0, width: 16, height: H * boy, backgroundColor: VURGU}} />
      <div style={{position: 'absolute', left: KENAR, top: 128, display: 'flex', alignItems: 'center', gap: 20}}>
        <div style={{backgroundColor: VURGU, color: KOYU, fontFamily: YAZI, fontWeight: 800, fontSize: 30, letterSpacing: 4,
          padding: '12px 22px', borderRadius: 6, whiteSpace: 'nowrap'}}>{label}</div>
        {by ? <div style={{fontFamily: YAZI, fontWeight: 600, fontSize: 26, color: '#ffffff', opacity: 0.9,
          textShadow: golge, whiteSpace: 'nowrap'}}>{by}</div> : null}
      </div>
    </AbsoluteFill>
  );
};

// Sayı kartı: bloğun üstünde tek büyük sayı ve kısa açıklaması (solda, altyazının üstünde).
const SayiKarti = ({value, label, frames}) => {
  const f = useCurrentFrame();
  const op = Math.min(interpolate(f, [0, 10], [0, 1], clamp), interpolate(f, [frames - 10, frames - 1], [1, 0], clamp));
  const kay = interpolate(f, [0, 14], [24, 0], {...clamp, easing: Easing.out(Easing.cubic)});
  return (
    <div style={{position: 'absolute', left: 130, top: 330, opacity: op, transform: `translateY(${kay}px)`}}>
      <div style={{position: 'absolute', left: -90, right: -120, top: -70, bottom: -70,
        background: 'radial-gradient(ellipse 60% 55% at 42% 50%, rgba(3,8,14,0.66) 0%, rgba(3,8,14,0.4) 50%, rgba(3,8,14,0) 100%)'}} />
      <div style={{position: 'relative', fontFamily: YAZI, fontWeight: 800, fontSize: 168, lineHeight: 1, color: VURGU,
        WebkitTextStroke: `10px ${KOYU}`, paintOrder: 'stroke fill', whiteSpace: 'nowrap',
        textShadow: '0 10px 26px rgba(0,0,0,0.6)'}}>{value}</div>
      {label ? <div style={{position: 'relative', fontFamily: YAZI, fontWeight: 600, fontSize: 40, letterSpacing: 3,
        color: '#ffffff', marginTop: 14, maxWidth: 820, lineHeight: 1.15, textShadow: golge}}>{label}</div> : null}
    </div>
  );
};

const kontur = ['-2px -2px', '2px -2px', '-2px 2px', '2px 2px', '0 -2px', '0 2px', '-2px 0', '2px 0']
  .map((o) => `${o} 0 ${KOYU}`).join(', ') + ', 0 5px 12px rgba(0,0,0,0.55)';

// Altyazı: en çok iki satır; konuşulan kelime vurgulu. Not bölümünde koyu bir panelin içinde durur.
const Altyazi = ({chunks}) => {
  const f = useCurrentFrame();
  const c = chunks.find((x) => f >= x.start && f < x.end);
  if (!c) return null;
  const op = interpolate(f - c.start, [0, 3], [0, 1], clamp);
  return (
    <div style={{position: 'absolute', left: 0, right: 0, top: ALTYAZI_Y, display: 'flex', justifyContent: 'center',
      transform: 'translateY(-50%)', opacity: op}}>
      <div style={{textAlign: 'center', padding: c.note ? '14px 34px 16px' : 0, borderRadius: 10,
        backgroundColor: c.note ? 'rgba(6,11,17,0.78)' : 'transparent',
        borderLeft: c.note ? `8px solid ${VURGU}` : 'none'}}>
        {c.lines.map((line, li) => (
          <div key={li} style={{lineHeight: 1.22, whiteSpace: 'nowrap'}}>
            {line.map((w, wi) => {
              const on = f >= w.s && f < w.e;
              return (
                <span key={wi} style={{display: 'inline-block', margin: '0 8px', fontFamily: YAZI, fontWeight: 800,
                  fontSize: 50, color: on ? VURGU : '#ffffff', textShadow: kontur}}>{w.t}</span>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
};

const HAREKET = ['in', 'right', 'out', 'left'];

export const Uzun = ({blocks = [], chunks = [], cards = [], notes = [], audio, label}) => (
  <AbsoluteFill style={{backgroundColor: '#05090e'}}>
    {blocks.map((b, i) => {
      const len = Math.max(1, b.end - b.start);
      const dur = len + (i < blocks.length - 1 ? GECIS : 0);
      return (
        <Sequence key={i} from={b.start} durationInFrames={dur}>
          <Gecis ilk={i === 0}>
            <Gorsel src={b.src} frames={dur} move={b.move || HAREKET[i % HAREKET.length]} />
          </Gecis>
        </Sequence>
      );
    })}
    <Katman />
    {notes.map((n, i) => (
      <Sequence key={`n${i}`} from={n.start} durationInFrames={Math.max(1, n.end - n.start)}>
        <NotSeridi label={n.label} by={n.by} frames={Math.max(1, n.end - n.start)} />
      </Sequence>
    ))}
    {blocks.map((b, i) => (b.stat ? (
      <Sequence key={`s${i}`} from={b.stat.start} durationInFrames={Math.max(1, b.stat.end - b.stat.start)}>
        <SayiKarti value={b.stat.value} label={b.stat.label} frames={Math.max(1, b.stat.end - b.stat.start)} />
      </Sequence>
    ) : null))}
    {cards.map((c, i) => {
      const fr = Math.max(1, c.end - c.start);
      return (
        <Sequence key={`c${i}`} from={c.start} durationInFrames={fr}>
          {c.kind === 'series' ? <SeriKarti tag={c.tag} name={c.name} title={c.title} frames={fr} />
            : c.kind === 'end' ? <BitisKarti kicker={c.kicker} title={c.title} frames={fr} />
              : <BolumKarti kicker={c.kicker} title={c.title} frames={fr} />}
        </Sequence>
      );
    })}
    <Filigran />
    {label ? <Etiket metin={label} /> : null}
    <Altyazi chunks={chunks} />
    {audio ? <Audio src={staticFile(audio)} /> : null}
  </AbsoluteFill>
);
