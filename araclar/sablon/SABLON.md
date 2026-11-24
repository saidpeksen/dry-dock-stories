# Shorts şablonu (Remotion)

Dry Dock Stories Shorts'ları için sabit görünüm: 1080×1920, 30 fps, soğuk renk ayarı, bölümler arası kısa
geçiş, sol üstte "DRY DOCK STORIES" filigranı, alt üçte birde kelime kelime vurgulu altyazı (konuşulan kelime
turuncu). Harita blokları `araclar/harita` bileşeniyle aynı videoda çizilir. Her şey bulutta çalışır, ücretsizdir.

## Kullanım

```
bash araclar/kur.sh                                   # ses modeli, paketler (harita ve şablon dahil)
python3 -I araclar/sablon/kurgu.py spec.json out      # → out/video.mp4, out/rapor.json
python3 -I araclar/sablon/kurgu.py spec.json out --still 30,300   # yalnız önizleme kareleri
```

`spec.json`, `make_short.py` ile aynıdır (`voice`, `blocks`: `image` ya da `map` + `image`, `text`).
Ses, seslendirme aralıkları ve ses düzeyi `make_short.py`'deki işlevlerle üretilir; yalnız görüntü şablondan gelir.
Şablon hata verirse `kurgu.py` sıfırdan farklı kodla çıkar; zamanlanmış görev o zaman `make_short.py` ile devam eder.

## Kelime zamanlaması

Kokoro modeli kelime süresi vermez. Her kelime fonemlerine ayrılır (ünlüler daha uzun sayılır), cümlenin gerçek
süresi bu ağırlıkla paylaştırılır; cümle içindeki virgül ve noktalar sesteki gerçek duraklamaya sabitlenir.
24 Kasım ölçümünde sapma çoğunlukla 0,1 sn civarı, en çok yaklaşık 0,25 sn.

## Dosyalar

| Dosya | İş |
|---|---|
| `kurgu.py` | Ses, kelime zamanları, altyazı parçaları, şablon girdisi (`sablon.json`), son kodlama |
| `render.mjs` | Remotion paketleme ve üretim (Chrome; `HARITA_CHROME` ile başka yol) |
| `src/Shorts.jsx` | Görünüm: görsel, harita, geçiş, renk katmanı, filigran, altyazı |
| `public/fonts/` | Montserrat (SIL Open Font License 1.1, `OFL.txt`) |

## Süre

2 çekirdekte 44 saniyelik video (bir harita bölümüyle) yaklaşık 5–6 dakika.

## Kabul testi (24 Kasım 2026)

Temiz klondan, bulut oturumunda, Ever Given örneğiyle (`araclar/harita/ornek-ever-given.json`): süre, çözünürlük,
ses düzeyi ve altyazı denetlendi. Sonuç `SABLON.md`'nin sonunda.

### Sonuç: geçti

- Temiz klon (cb18369), `kur.sh` 10 sn (harita ve şablon paketleri kuruldu), `kurgu.py` 6 dk.
- Video: 44,1 sn; 1080×1920; 30 fps; H.264 yuv420p (standart aralık); AAC 48 kHz.
- Ses düzeyi: −15,2 LUFS (hedef −17 ile −13), tepe −4,4 dBFS.
- Altyazı: 29 parça, 119 kelime; karelerde okunuyor, konuşulan kelime vurgulu, alt üçte birde. Filigran sol üstte.
- Harita bölümü (blok 2) şablonun içinde çizildi.
