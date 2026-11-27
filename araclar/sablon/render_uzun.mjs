// Uzun video şablonunu üretir (kurgu_uzun.py çağırır). Paketleme bir kez yapılır; parçalar sırayla üretilir.
//   node render_uzun.mjs props.json PUBLIC_DIZINI --parcalar parcalar.json   → her parça için ayrı MP4 (sessiz)
//   node render_uzun.mjs props.json PUBLIC_DIZINI --still 120,900 CIKIS_DIZINI → kare-120.png, kare-900.png
// parcalar.json: [{"ad": "p000", "ilk": 0, "son": 899, "cikis": "/tam/yol/p000_ham.mp4"}, …]  (son dahil)
// Var olan çıkış atlanır: yarım kalan iş aynı komutla kaldığı yerden sürer. Her parça bitince bir JSON satırı yazılır.
// Ortam: SABLON_ESZAMANLI (varsayılan 2), UZUN_KARE (jpeg | png; varsayılan jpeg), HARITA_CHROME (Chrome yolu).
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';

const here = path.dirname(fileURLToPath(import.meta.url));
const nm = path.join(here, 'node_modules');
const [, , propsPath, publicDir, flag, arg, stillDir] = process.argv;
if (!propsPath || !publicDir || !['--parcalar', '--still'].includes(flag) || !arg) {
  console.error('kullanım: node render_uzun.mjs props.json PUBLIC_DIZINI --parcalar parcalar.json | --still KARELER CIKIS_DIZINI');
  process.exit(2);
}
const inputProps = JSON.parse(fs.readFileSync(propsPath, 'utf8'));
const browserExecutable = process.env.HARITA_CHROME ||
  ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find((p) => fs.existsSync(p));
if (!browserExecutable) { console.error('HATA: Chrome bulunamadı'); process.exit(3); }
const common = {browserExecutable, chromeMode: 'chrome-for-testing', logLevel: 'error'};
const kare = process.env.UZUN_KARE === 'png' ? 'png' : 'jpeg';

const t0 = Date.now();
const serveUrl = await bundle({
  entryPoint: path.join(here, 'src', 'uzun', 'index.jsx'),
  publicDir: path.resolve(publicDir),
  onProgress: () => {},
  webpackOverride: (c) => ({
    ...c,
    resolve: {
      ...c.resolve,
      modules: [nm, 'node_modules'],
      alias: {...(c.resolve && c.resolve.alias), react: path.join(nm, 'react'), 'react-dom': path.join(nm, 'react-dom'),
        remotion: path.join(nm, 'remotion')},
    },
  }),
});
const composition = await selectComposition({...common, serveUrl, id: 'Uzun', inputProps});
console.log(JSON.stringify({asama: 'paket', sn: (Date.now() - t0) / 1000, kare_sayisi: composition.durationInFrames}));

if (flag === '--still') {
  for (const fr of arg.split(',').map(Number)) {
    const out = path.join(path.resolve(stillDir || '.'), `kare-${fr}.png`);
    await renderStill({...common, composition, serveUrl, inputProps, output: out, frame: fr, imageFormat: 'png'});
    console.log(JSON.stringify({asama: 'kare', kare: fr, cikis: out}));
  }
} else {
  const parcalar = JSON.parse(fs.readFileSync(arg, 'utf8'));
  for (const p of parcalar) {
    if (fs.existsSync(p.cikis)) { console.log(JSON.stringify({asama: 'parca', ad: p.ad, atlandi: true})); continue; }
    const t1 = Date.now();
    const tmp = p.cikis.replace(/\.mp4$/, '') + '.yarim.mp4';   // yarım kalan dosya tam sanılmasın
    await renderMedia({
      ...common, composition, serveUrl, inputProps, codec: 'h264', crf: 12, pixelFormat: 'yuv420p', x264Preset: 'veryfast',
      muted: true, imageFormat: kare, ...(kare === 'jpeg' ? {jpegQuality: 95} : {}),
      frameRange: [p.ilk, p.son], concurrency: Number(process.env.SABLON_ESZAMANLI || 2), outputLocation: tmp,
    });
    fs.renameSync(tmp, p.cikis);
    console.log(JSON.stringify({asama: 'parca', ad: p.ad, kare: p.son - p.ilk + 1, sn: (Date.now() - t1) / 1000}));
  }
}
console.log(JSON.stringify({asama: 'bitti', sn: (Date.now() - t0) / 1000}));
