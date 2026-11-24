// Harita bölümünü üretir.
//   node render.mjs harita.json cikis.mp4            → video (props.frames kare, 1080x1920, 30 fps)
//   node render.mjs harita.json kare.png --still 120 → tek kare (önizleme)
// Tarayıcı: HARITA_CHROME ortam değişkeni, yoksa sistemdeki Chrome for Testing.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {renderMedia, renderStill, selectComposition} from '@remotion/renderer';

const here = path.dirname(fileURLToPath(import.meta.url));
const [, , propsPath, out, flag, frameArg] = process.argv;
if (!propsPath || !out) { console.error('kullanım: node render.mjs harita.json cikis.mp4 [--still KARE]'); process.exit(2); }

const inputProps = JSON.parse(fs.readFileSync(propsPath, 'utf8'));
const browserExecutable = process.env.HARITA_CHROME ||
  ['/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'].find((p) => fs.existsSync(p));
if (!browserExecutable) { console.error('HATA: Chrome bulunamadı'); process.exit(3); }
const common = {browserExecutable, chromeMode: 'chrome-for-testing', logLevel: 'error'};

const serveUrl = await bundle({entryPoint: path.join(here, 'src', 'index.jsx'), onProgress: () => {}});
const composition = await selectComposition({...common, serveUrl, id: 'Harita', inputProps});

if (flag === '--still') {
  await renderStill({...common, composition, serveUrl, inputProps, output: out, frame: Number(frameArg || 0), imageFormat: 'png'});
} else {
  const tmp = out.replace(/\.mp4$/, '') + '.yarim.mp4';   // yarım kalan dosya tam sanılmasın
  await renderMedia({
    ...common, composition, serveUrl, inputProps, codec: 'h264', crf: 10, pixelFormat: 'yuv420p',
    imageFormat: 'jpeg', jpegQuality: 95, concurrency: Number(process.env.HARITA_ESZAMANLI || 2),
    outputLocation: tmp, muted: true,
  });
  fs.renameSync(tmp, out);
}
console.log(JSON.stringify({ok: true, out, frames: composition.durationInFrames}));
