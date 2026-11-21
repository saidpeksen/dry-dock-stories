# Dry Dock Stories

Yayına hazırlanan videoların geçici aktarım deposu. Videolar yayınlandıktan sonra buradan kaldırılır.

- `videolar/NN-konu/video.mp4` — onay bekleyen ya da yayına gidecek tam kalite video.
- `araclar/kur.sh` — kurgu ortamını hazırlar (ses modeli, Python paketleri).
- `araclar/make_short.py` — metin + 5 görselden 1080×1920 video üretir.
  Kullanım: `bash araclar/kur.sh && python3 -I araclar/make_short.py spec.json cikis`
- `durum.json` — üretim hattının durumu (biçim: `araclar/DURUM.md`; denetim: `araclar/durum_denetle.py`).
