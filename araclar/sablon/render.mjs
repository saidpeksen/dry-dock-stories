// Shorts şablonunu üretir (kurgu.py çağırır).
//   node render.mjs props.json cikis.mp4 PUBLIC_DIZINI              → video (ses dahil)
//   node render.mjs props.json kare.png PUBLIC_DIZINI --still 120  → tek kare
// PUBLIC_DIZINI: işin görselleri, ses.wav ve fonts/ klasörü (kurgu.py hazırlar).
// Harita bileşeni ../harita/src'den alınır; react ve remotion tek kopya olsun diye bu klasörün paketlerine bağlanır.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';

const here = path.dirname(fileURLToPath(import.meta.url));
const nm = path.join(here, 'node_modules');
const [, , propsPath, out, publicDir, flag, frameArg] = process.argv;
if (!propsPath || !out || !publicDir) {
  console.error('kullanım: node render.mjs props.json cikis.mp4 PUBLIC_DIZINI [--still KARE]');
  process.exit(2);
}
const inputProps = JSON.parse(fs.readFileSync(propsPath, 'utf8'));
const browserExecutable = process.env.HARITA_CHROME ||
  ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find((p) => fs.existsSync(p));
if (!browserExecutable) { console.error('HATA: Chrome bulunamadı'); process.exit(3); }
const common = {browserExecutable, chromeMode: 'chrome-for-testing', logLevel: 'error'};

const serveUrl = await bundle({
  entryPoint: path.join(here, 'src', 'index.jsx'),
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
const composition = await selectComposition({...common, serveUrl, id: 'Shorts', inputProps});

if (flag === '--still') {
  await renderStill({...common, composition, serveUrl, inputProps, output: out, frame: Number(frameArg || 0), imageFormat: 'png'});
} else {
  const tmp = out.replace(/\.mp4$/, '') + '.yarim.mp4';   // yarım kalan dosya tam sanılmasın
  await renderMedia({
    ...common, composition, serveUrl, inputProps, codec: 'h264', crf: 12, pixelFormat: 'yuv420p', x264Preset: 'veryfast',
    audioCodec: 'aac', audioBitrate: '160k', imageFormat: 'jpeg', jpegQuality: 95,
    concurrency: Number(process.env.SABLON_ESZAMANLI || 2), outputLocation: tmp,
  });
  fs.renameSync(tmp, out);
}
console.log(JSON.stringify({ok: true, out, frames: composition.durationInFrames}));
