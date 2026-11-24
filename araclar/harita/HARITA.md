# Harita bölümü

`make_short.py` içinde bir blok, görsel yerine harita animasyonu olabilir. Harita Remotion ile
(React + d3-geo, kara verisi `world-atlas`) bulutta çizilir. Ücretsizdir, dış servis kullanmaz.
Gereken: Node 18+, sistemde Chrome (`/usr/bin/google-chrome`; başka yer için `HARITA_CHROME`).
`node_modules` yoksa `make_short.py` ilk harita bloğunda `npm ci` çalıştırır (yaklaşık 20 sn).

Harita üretilemezse ve blokta `"image"` de varsa o görselle devam edilir; rapor.json'daki `harita`
alanı ne olduğunu yazar. Yalnız `"map"` varsa kurgu hata verir.

## spec.json içinde

```json
{"map": {...}, "image": "2.jpg", "text": "March 2021. The Ever Given ... through the Suez Canal."}
```

Bütün zamanlar bölüm uzunluğuna göre 0–1 arası orandır. Kare sayısını `make_short.py` sesin
süresine göre kendisi verir.

| Alan | Anlamı |
|---|---|
| `camera` | `[{t, lon, lat, zoom}]` kamera durakları. `zoom` 1: bütün küre; 7: bölge (Mısır ve Kızıldeniz); 25+: tek kanal ya da liman. Duraklar arası büyük daire boyunca, yumuşak geçiş. |
| `route` | `{points: [[lon, lat], ...], start, end}` turuncu rota; `start`–`end` arasında ilerleyerek çizilir, ucunda gemi işareti. Noktalar denizde olmalı. |
| `lines` | `[{points, at, color?, width?}]` sabit çizgiler (ör. kanalın kendisi; 10m kara verisinde kanal yok). |
| `markers` | `[{lon, lat, at, label?, dx?, dy?, anchor?}]` atan kırmızı işaret; yazı varsayılan olarak sağında. |
| `labels` | `[{text, kind, lon, lat, at, until?, dx?, dy?, anchor?}]` `kind`: `sea`, `land`, `water`, `place`. |
| `dots` | `[{lon, lat}]` ve `at`, `stagger`: sırayla beliren noktalar (ör. bekleyen gemiler). |
| `tag` | Üstte tarih etiketi (ör. `"MARCH 2021"`), `tag_at`. |

Yerleşim: odak noktası ekranın üst yarısında (y≈760); alt üçte bir altyazıya ayrılmıştır, sağ kenar
Shorts düğmelerinin altında kalır. Önemli yer adlarını ve işareti odak çevresine koy.

## Kurallar

- Her koordinat ve olgu iki kaynaktan doğrulanır (ör. Ever Given: 30.0175 K, 32.58 D; kuzeye giderken).
- Haritada gerçek yer adları olabilir; gemi ya da şirket adı, logo yazılmaz.
- Önizleme karesi: `node render.mjs harita.json kare.png --still 120`
- Süre: 1080×1920'de saniyede yaklaşık 3 kare (2 çekirdek); 8 saniyelik bölüm yaklaşık 1,5 dakika.

## Örnek

Ever Given (Shorts 03'ün yeniden kurgusu, 24 Kasım denemesi): `ornek-ever-given.json`.
