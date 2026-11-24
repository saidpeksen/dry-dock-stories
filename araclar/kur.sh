#!/usr/bin/env bash
# Kurgu ortamı: Kokoro ses modeli + Python paketleri. Yinelenebilir; hazır olanı atlar.
set -euo pipefail
D=/home/claude/tts/models   # make_short.py bu yolu bekler
U=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
mkdir -p "$D"
python3 -c "import kokoro_onnx, soundfile" 2>/dev/null || pip install -q --break-system-packages kokoro-onnx==0.6.1 soundfile
indir() {  # ad, beklenen sha256
  if [ -f "$D/$1" ] && echo "$2  $D/$1" | sha256sum -c --status; then return 0; fi
  curl -fsSL -o "$D/$1" "$U/$1"
  echo "$2  $D/$1" | sha256sum -c --status || { echo "HATA: $1 sha256 uyuşmuyor"; exit 1; }
}
indir kokoro-v1.0.onnx 7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5
indir voices-v1.0.bin bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d
command -v ffmpeg >/dev/null || { echo "HATA: ffmpeg yok"; exit 1; }
SUZGEC=$(ffmpeg -hide_banner -filters 2>/dev/null || true)
for f in ass zoompan loudnorm; do
  grep -q " $f " <<<"$SUZGEC" || { echo "HATA: ffmpeg '$f' süzgeci yok"; exit 1; }
done
YAZI=$(fc-list 2>/dev/null || true)
grep -qi "DejaVu Sans" <<<"$YAZI" || { echo "HATA: DejaVu Sans yazı tipi yok"; exit 1; }
# Harita bölümü (isteğe bağlı): yoksa harita blokları görsele düşer.
if command -v node >/dev/null && { [ -n "${HARITA_CHROME:-}" ] || [ -x /usr/bin/google-chrome ] || [ -x /usr/bin/chromium ]; }; then
  A="$(cd "$(dirname "$0")" && pwd)"
  for P in harita sablon; do
    [ -d "$A/$P/node_modules" ] || (cd "$A/$P" && npm ci --no-audit --no-fund --loglevel=error >/dev/null)
  done
  echo "harita ve şablon: hazır (node, Chrome, paketler)"
else
  echo "UYARI: node ya da Chrome yok; şablon kullanılamaz (make_short.py ile devam), harita blokları görsele düşer"
fi
echo "kurgu ortamı hazır"
