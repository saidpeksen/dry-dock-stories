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

## İlk kare başlığı ve köşe etiketi (isteğe bağlı)

`spec.json`'a üç alan eklenebilir. Hiçbiri yoksa çıktı önceki sürümle bayt bayt aynıdır.

```json
{"voice": "am_michael", "headline": "CUT IN HALF", "label": true, "blocks": [ … ]}
```

| Alan | Değer | Ne yapar |
|---|---|---|
| `headline` | 2–4 kelime | İlk kareden itibaren 1,5 saniye, blok 1 görselinin üstünde büyük yazı. Büyük harfe çevrilir. |
| `headline_y` | sayı (piksel), varsayılan 480 | Başlığın orta yüksekliği. Başlık görselin ana konusunu kapatıyorsa kaydırmak için. |
| `label` | `true` ya da metin | Sağ üstte, filigranla aynı hizada küçük yazı; video boyunca. `true` → "AI reconstruction". |

- Başlık en çok üç satıra bölünür. Yazının gerçek genişliği ölçülür; 940 piksele sığan en büyük boyut seçilir
  (en çok 150 px). 120 px'e ulaşan en az satırlı bölme tercih edilir.
- Başlık 190–1150 piksel bandında kalır: filigran ve etiketin altında, altyazının üstünde. `headline_y` başlığı bu
  bandın dışına çıkaramaz.
- İlk karede tam görünür (giriş geçişi yoktur), son 0,2 saniyede söner.
- Kelime sayısı 2–4 dışındaysa ya da alan bozuksa kurgu durmaz; `rapor.json`'da `uyarilar` listesine yazılır.
  Çizilen başlık ve etiket `rapor.json`'da `baslik` ve `etiket` olarak görünür.
- Yedek hat (`make_short.py`) bu alanları kabul eder ama çizmez; `rapor.json`'da `uyarilar`'a yazar.
- İlk kareye bakmak için: `--still 0,20,44`.

## Kelime zamanlaması

Kokoro modeli kelime süresi vermez. Her kelime fonemlerine ayrılır (ünlüler daha uzun sayılır), cümlenin gerçek
süresi bu ağırlıkla paylaştırılır; cümle içindeki virgül ve noktalar sesteki gerçek duraklamaya sabitlenir.
24 Kasım ölçümünde sapma çoğunlukla 0,1 sn civarı, en çok yaklaşık 0,25 sn.

## Dosyalar

| Dosya | İş |
|---|---|
| `kurgu.py` | Ses, kelime zamanları, altyazı parçaları, şablon girdisi (`sablon.json`), son kodlama |
| `render.mjs` | Remotion paketleme ve üretim (Chrome; `HARITA_CHROME` ile başka yol) |
| `src/Shorts.jsx` | Görünüm: görsel, harita, geçiş, renk katmanı, filigran, altyazı, ilk kare başlığı, köşe etiketi |
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

## Kabul testi: ilk kare başlığı ve köşe etiketi (26 Kasım 2026)

04'ün PAKET metni ve görselleriyle (köprü, `04-air-pocket`), bulut oturumunda, 2 çekirdekte.

### Sonuç: geçti

- Alan yokken çıktı aynı: değişiklikten önceki kodla (4a3626c) ve yeni kodla üretilen `video.mp4` bayt bayt aynı
  (sha256 `01e3d962…a77ff0`, 32,8 MB). Şablon girdisi (`sablon.json`) ve ses de aynı.
- Başlıklı deneme (`"headline": "Trapped underwater", "label": true`): 39,6 sn; 1080×1920; 30 fps; H.264 yuv420p
  (standart aralık); AAC 48 kHz; 33,2 MB; `kurgu.py` 3 dk.
- Ses düzeyi: −15,4 LUFS (hedef −17 ile −13), tepe −4,3 dBFS.
- Altyazı: 27 parça, 102 kelime; alt üçte birde, konuşulan kelime vurgulu.
- Başlık: 0. karede tam görünüyor (iki satır), 44. karede yok. Filigran, etiket ve altyazıyla çakışmıyor;
  `headline_y` 0 ve 5000 verildiğinde de bandın içinde kalıyor.
- Etiket: her bloktan alınan karede sağ üstte. 600. karede başlıksız kareden tek fark etiketin kutusu
  (x 787–1027, y 96–126).
- Bölme denemeleri (ilk kare): CUT IN HALF ve SUNK tek satır; A HAND MOVED, TRAPPED UNDERWATER ve CAPSIZED AT THE
  PIER iki satır; sekiz kelimelik metin üç satır. Hiçbiri taşmadı.
- Yedek hat: aynı spec ile `make_short.py` hatasız bitti (1 dk 20 sn); başlık ve etiket çizilmedi, `rapor.json`'da
  uyarı var. Videosu eski kodun alansız çıktısıyla bayt bayt aynı.
