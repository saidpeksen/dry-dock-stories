# Uzun video şablonu (Remotion, yatay)

Dry Dock Stories uzun videoları için sabit görünüm: 1920×1080, 30 fps. Shorts şablonuyla aynı dil (soğuk renk
ayarı, sol üstte "DRY DOCK STORIES" filigranı, sağ üstte köşe etiketi, konuşulan kelimesi vurgulu altyazı) ve uzun
videoya özgü parçalar: bölüm kartı, seri kartı, "tersaneden bakınca" şeridi, sayı kartı, bitiş kartı.

Bu şablon Shorts şablonundan bağımsızdır: ayrı giriş noktası (`src/uzun/`), ayrı üretim betiği (`render_uzun.mjs`),
ayrı kurgu aracı (`kurgu_uzun.py`). Shorts dosyalarının hiçbiri değişmedi.

Durum (27 Kasım 2026): **deneme**. Zamanlanmış görev bu aracı kullanmıyor; ilk gerçek uzun videodan önce Said'in
kararı gerekir (aktarım yolu, kodlama ayarı). Ölçümler en altta.

## Kullanım

```
bash araclar/kur.sh                                                  # ses modeli, paketler
python3 -I araclar/sablon/kurgu_uzun.py spec.json out                # → out/video.mp4, out/rapor.json
python3 -I araclar/sablon/kurgu_uzun.py spec.json out --still 0,900  # yalnız önizleme kareleri (out/kare-N.png)
python3 -I araclar/sablon/kurgu_uzun.py spec.json out --yalniz-ses   # yalnız ses ve süre
```

Kurgu uzun sürer (aşağıda). Komut arka planda çalıştırılır ve `out/uretim.log` izlenir. Yarıda kesilirse aynı komut
kaldığı yerden sürer: cümle sesleri (`out/ses_onbellek/`) ve bitmiş parçalar (`out/parcalar/<kimlik>/`) saklanır.
Spec ya da görsel değişirse kimlik değişir ve parçalar yeniden üretilir.

## spec.json

Örnek: `ornek-uzun-kuru-havuz.json` (kuru havuza alma, 45 blok, 1.338 kelime, yaklaşık 8 dakika). Görseller spec
dosyasının yanında durur; depoya konmaz.

```json
{"voice": "am_michael", "label": true,
 "title": "What Really Happens to a Giant Ship in Dry Dock?",
 "series": {"name": "IN THE DRY DOCK", "tag": "A DRY DOCK STORIES SERIES"},
 "sections": [
  {"kind": "cold", "chapter": "The question", "blocks": [{"image": "01.jpg", "text": "…"}]},
  {"kind": "roadmap", "card": "series", "blocks": [{"image": "04.jpg", "text": "…"}]},
  {"title": "Why a ship has to leave the water", "blocks": [
    {"image": "08.jpg", "text": "…", "stat": {"value": "20–25%", "label": "MORE EMISSIONS FROM A THIN LAYER OF SLIME"}}]},
  {"kind": "note", "title": "From the shipyard floor", "by": "…", "blocks": [{"image": "31.jpg", "text": "…"}]},
  {"kind": "close", "chapter": "The answer", "end": {"kicker": "NEXT IN THE DRY DOCK", "title": "…"},
   "blocks": [{"image": "44.jpg", "text": "…"}]}
 ]}
```

| Alan | Ne yapar |
|---|---|
| `sections[].blocks[]` | Bir blok bir görseldir (`image`) ve o görselin üstünde okunan metindir (`text`; bir ya da birkaç cümle). |
| `sections[].title` | Bölüm kartı: bölümün başında 2,6 saniye, ilk görselin üstünde "PART n" ve başlık. `kicker` ile "PART n" değiştirilir. |
| `sections[].card: "series"` | Bölümün başında seri kartı: `series.tag`, `series.name` ve videonun `title` alanı. |
| `sections[].kind: "note"` | "Tersaneden bakınca" bölümü: solda renkli dikey şerit, üstte etiket (`label`, varsayılan "FROM THE SHIPYARD FLOOR") ve yanında `by`; altyazı koyu panelde. Bölüm kartı çıkmaz. |
| `blocks[].stat` | Sayı kartı: `value` (büyük, turuncu) ve `label`; bloğun seslendirmesi boyunca solda. |
| `sections[].end` | Bitiş kartı: bölümün son bloğundan videonun sonuna kadar; solda `kicker` ve `title`, sağ yarı YouTube bitiş ekranı öğeleri için boş. Seslendirme bittikten sonra 6 saniye daha kalır. |
| `sections[].chapter` | Yalnız `rapor.json`'daki bölüm işaretleri için ad (açıklamaya yazılacak zaman damgaları). Başlıklı bölümlerde başlık kullanılır. |
| `blocks[].move` | Görsel hareketi: `in`, `out`, `left`, `right`. Verilmezse sırayla değişir. |
| `label` | Köşe etiketi; `true` → "AI reconstruction". |
| `kodlayici`, `crf`, `preset` | Son kodlama: `x264` (varsayılan; crf 18, medium) ya da `x265` (crf 19, medium). Bkz. "Kodlama ve ortam" ve ölçümler. |
| `parca_kare` | Bir parçanın kare sayısı (varsayılan 900 = 30 saniye). |
| `parca_mb` | Verilirse ana kopya baytları değişmeden bu boyutta parçalara bölünür (`video-parca-NN.bin`, `video-parcalar.json`). |
| `onizleme` | `true` ise 720p izleme kopyası da üretilir (`onizleme.mp4`; yayınlanmaz). |

Bölüm türleri (`kind`) yalnız `note` için görünüşü değiştirir; `cold`, `roadmap`, `close` okunurluk içindir.
Bölüm sayısı ve sırası serbesttir: süreç videosu adım sırasıyla, olay videosu zaman çizgisiyle kurulabilir.

## Görseller

- Yatay, 1536×1024 (ChatGPT'nin yatay boyutu). Şablon görseli 1920×1080'e sığdırır: üstten ve alttan toplam yüzde
  16 kırpılır. Önemli ayrıntı üst ve alt kenara yaslanmamalı.
- Alt beşte bir altyazı içindir; sol üst ve sağ üst köşede filigran ve etiket durur.
- Blok başına bir görsel; aynı görsel birden çok blokta kullanılabilir (dosya bir kez kopyalanır).
- Sipariş (deneme düzeni): köprü klasörünün kökünde `U00-SIPARIS-UZUN` belgesi; görseller de köke
  `U00-01.jpg` … adıyla gelir. Köprüde uzun video için alt klasör açılmaz: zamanlanmış görev köprüdeki her alt
  klasörü bir Shorts sayar ve yeni Shorts siparişini engeller. Kalıcı düzen canlıya geçişte kararlaştırılacak.

## Dosyalar

| Dosya | İş |
|---|---|
| `kurgu_uzun.py` | Ses, kelime zamanları, altyazı parçaları, şablon girdisi (`sablon.json`), parça parça üretim, kodlama, birleştirme, rapor |
| `render_uzun.mjs` | Remotion paketleme (bir kez) ve parçaların sırayla üretimi; `--still` ile tek kare |
| `src/uzun/Uzun.jsx` | Görünüm: görsel, geçiş, renk katmanı, filigran, etiket, altyazı, kartlar, şerit |
| `ornek-uzun-kuru-havuz.json` | Deneme metni (kaynakları aşağıda) |

## Kodlama ve ortam

Bulut oturumundaki `ffmpeg` bir başlatıcıdır (`/usr/local/bin/ffmpeg`): x264 için `-preset fast | medium | slow`
verilen komutu `veryfast` ve 3 düşük CRF ile çalıştırır (daha az işlemci, daha büyük dosya). Yani araçlardaki
"crf 18, medium" bu ortamda gerçekte "crf 15, veryfast" olarak kodlanır; Shorts videoları da böyle üretiliyor.
Gerçek ön ayar için `/usr/bin/ffmpeg` tam yoluyla çağrılır ya da `SANDBOX_FFMPEG_VERYFAST_FOR_NAMED_PRESET=0`
verilir. x265 ve AV1 bu başlatıcıdan etkilenmez. Ayrıntı: `strings /usr/local/bin/ffmpeg`.

## Ölçümler (27 Kasım 2026)

Ortam: bulut oturumu, 2 çekirdek, 7 GB bellek. Görseller geçicidir: köprüdeki eski Shorts görselleri (04 ve 05)
1536×1024'e çevrilerek kullanıldı; gerçek yatay görsellerle boyut biraz değişebilir.

### Tam uzunluk (`ornek-uzun-kuru-havuz.json`, 45 blok, 1.344 kelime)

| Ölçü | Değer |
|---|---|
| Video | 7 dk 56 sn (475,8 sn), 14.273 kare, 1920×1080, 30 fps, H.264 yuv420p (standart aralık), AAC 48 kHz |
| Ses üretimi | 6,6 dk (aynı anda başka bir kodlama çalışıyordu) |
| Şablon üretimi | 37,6 dk: 16 parça, parça başına 127–157 sn (yaklaşık 6,3 kare/sn) |
| Kodlama | 4,5 dk |
| Birleştirme | 10 sn |
| 720p izleme kopyası | 2 dk; 30,1 MB |
| Toplam | 50,9 dk (video dakikası başına yaklaşık 6,4 dk) |
| Dosya | 353,0 MB (336,7 MiB), 5,94 Mbit/s (video dakikası başına yaklaşık 44,5 MB) |
| Ses düzeyi | −15,3 LUFS (hedef −17 ile −13), tepe −1,2 dBFS |
| Aktarım parçaları | 4 (95 + 95 + 95 + 68 MB); uç uca eklenince sha256 ana kopyayla aynı |

Aynı oranla tahmin (ölçülmedi): 10 dk yaklaşık 445 MB ve 64 dk kurgu; 15 dk yaklaşık 670 MB ve 96 dk; 20 dk yaklaşık
890 MB ve 128 dk.

Gerçek yatay görsellerle (45 görsel, 1536×1024 JPEG) aynı metin yeniden kuruldu (27 Kasım 2026): 7 dk 56 sn,
363,0 MB (346,2 MiB), 6,10 Mbit/s; şablon üretimi 39,8 dk (parça başına 136–157 sn), kodlama 5,3 dk, birleştirme
12 sn, 720p izleme kopyası 2,2 dk ve 31,7 MB; ses önbellekten 27 sn; toplam 48,0 dk. Ses düzeyi −15,3 LUFS, tepe
−1,2 dBFS. Dosya geçici görsellerle çıkandan yüzde 3 büyük; 95 MB'lık parçayla yine 4 parça.

### Kısa ölçümler (38,4 sn, aynı metin)

| Değişken | Boyut | Bit hızı | Şablon üretimi |
|---|---|---|---|
| Görsel 1536×1024, JPEG ara kare (varsayılan) | 33,2 MB | 6,92 Mbit/s | 189 sn |
| Görsel 1024×576 kırpma (daha az ayrıntı) | 28,1 MB | 5,86 Mbit/s | 187 sn |
| PNG ara kare (`UZUN_KARE=png`) | 29,0 MB | 6,05 Mbit/s | 318 sn |

### Son kodlama seçenekleri (aynı 30 sn'lik ham parça; kalite ham parçaya göre)

| Kodlama | Boyut | Oran | Süre | PSNR (dB) | SSIM |
|---|---|---|---|---|---|
| Bugünkü: araçta crf 18 medium, ortamda crf 15 veryfast | 24,86 MB | 1,00 | 19 sn | 47,90 | 0,99215 |
| x264 crf 18 medium (gerçek ön ayar) | 18,59 MB | 0,75 | 97 sn (yük altında) | 47,92 | 0,99193 |
| x264 crf 18 veryslow | 16,00 MB | 0,64 | 236 sn | 48,15 | 0,99232 |
| x264 araçta crf 20 medium, ortamda crf 17 veryfast | 16,26 MB | 0,65 | 18 sn | 46,66 | 0,99019 |
| x265 crf 18 medium | 14,37 MB | 0,58 | 69 sn | 48,39 | 0,99201 |
| x265 crf 20 medium | 9,76 MB | 0,39 | 63 sn | 47,41 | 0,99043 |
| x265 crf 22 medium | 6,61 MB | 0,27 | 59 sn | 46,41 | 0,98854 |
| AV1 (SVT) crf 28, ön ayar 6 | 5,81 MB | 0,23 | 136 sn | 47,63 | 0,99130 |

- Aynı ölçülen kalitede en küçük dosyayı x265 veriyor (yaklaşık yarı boyut, kodlama yaklaşık 3,5 kat). YouTube'un
  desteklenen biçim listesinde HEVC (h265) var; AV1 o listede yazmıyor.
- Hiçbir seçenek 8 dakikalık videoyu aynı kalitede 100 MiB'ın altına indirmiyor (gereken yaklaşık 1,7 Mbit/s).
- `spec.json`'da `"kodlayici": "x265"` (varsayılan crf 19) ile seçilir. Varsayılan x264'tür (Shorts ile aynı ayar).

### Tam uzunluk, HEVC (`"kodlayici": "x265"`, crf 19 medium; aynı ham parçalardan)

| Ölçü | H.264 (bugünkü ayar) | HEVC crf 19 |
|---|---|---|
| Dosya | 353,0 MB (336,7 MiB), 5,94 Mbit/s | 154,4 MB (147,2 MiB), 2,60 Mbit/s |
| Kodlama süresi | 4,5 dk | 17,0 dk |
| Aktarım parçası (95 MB) | 4 | 2 |
| Kalite, 1. parça (PSNR / SSIM) | 47,80 dB / 0,99211 | 47,94 dB / 0,99148 |
| Kalite, 9. parça (PSNR / SSIM) | 48,11 dB / 0,99184 | 47,80 dB / 0,99036 |

HEVC crf 19, bugünkü ayarla aynı düzeyde PSNR veriyor; SSIM binde bir kadar düşük. Fark istenmiyorsa crf 18
(30 sn'lik ölçümde PSNR 48,39 dB, SSIM 0,99201; boyut oranı 0,58). Parçalar `-c copy` ile birleşti; birleşmiş
dosya `hvc1` etiketli, 14.273 kare. YouTube'a yükleme denenmedi.

### Aktarım (100 MiB üstü dosya)

| Yol | Sonuç |
|---|---|
| GitHub, tek dosya | Sınır 100 MiB; 7 dk 56 sn'lik video 336,7 MiB |
| GitHub, 95 MB'lık parçalar, geçici dal (`aktarim-deneme-u00`) | Çalıştı: 4 parça toplam 30 sn'de gönderildi (parça başına 6–8 sn), 17 sn'de geri indirildi; bayt sayıları ve sha256 aynı |
| Git LFS | Bu oturum türünden yüklenemedi: LFS depolama adresi oturumun ağ izninde değil |
| Google Drive (bağlayıcı) | Çağrı başına 4,2 MB sınırı; 5 MB'lık dosya reddedildi |
| GitHub Releases | Bu oturum türünde kullanılamıyor (21 Kasım denemesi) |

Parçalı aktarımda alıcı parçaları ad sırasıyla uç uca ekler (`cat video-parca-*.bin > video.mp4`) ve
`video-parcalar.json`'daki `toplam_bayt` ile `sha256` değerini karşılaştırır. Geçici dal, video yayınlanıp
arşivlenince silinir; `main` dalının geçmişi büyümez.

### Bakılan kareler

Tam uzunluktaki videodan 12 kare (açılış, yol haritası, üç bölüm kartı, sayı kartı, şerit, bitiş kartı):
filigran sol üstte, etiket sağ üstte, altyazı alt üçte birde ve konuşulan kelime vurgulu; kartlar ve şerit doğru
bölümlerde. Altyazı bölmesi bazı cümlelerde kelime öbeğini ayırıyor (ör. "three football / fields").

### Doğrulanmayanlar

- Gerçek yatay görseller (45 adet) henüz yok; görünüş kararı için gerçek görsellerle yeniden kurgu gerekir.
- ChatGPT'nin parçaları indirip birleştirmesi ve birleşmiş dosyayı Studio'ya yüklemesi denenmedi.
- Zamanlanmış görev oturumunda 50 dakikalık kurgu denenmedi (bu ölçüm sohbet oturumunda, arka planda yapıldı).
- HEVC dosyanın YouTube'a yüklenmesi denenmedi.
- Yatay harita bölümü yok (`araclar/harita` 1080×1920'ye göre yazılı).
- Pusulab'da uzun video önizlemesi (80 MB sınırı; 720p kopya sığıyor, sunucu ana kopya yerine onu göstermeli).

## Deneme metninin kaynakları

Metin denemedir ve yayınlanmadı; "tersaneden bakınca" bölümü yer tutucudur. Olgular şu kaynaklarla denetlendi:

- Dip incelemesi, beş yılda en az iki kez, en çok 36 ay arayla (SOLAS I/10): Lloyd's Register Class News 10/13;
  IMO HSSC inceleme kılavuzu.
- 0,5 mm slime, gövdenin yüzde 50'sine kadar, yüzde 20–25 sera gazı artışı: IMO (GloFouling, 2021 ön sonuçları);
  The Maritime Executive.
- Omurga takozları yanaşma planına göre dizilir; beton ya da çelik gövde, üstte ahşap: Marine Insight; Maritime
  Reporter (Aralık 1987); ABD donanması UFC 4-213-10.
- Kritik dönem (kıçın takoza değmesinden geminin bütünüyle oturmasına kadar), sanal GM kaybı, kıça trimli giriş,
  pompalamanın yavaşlatılması: Marine Insight; ABD donanması hasar kontrol eğitimi (FAS).
- Havuz işleri (yıkama, raspa, boya, anot, kinistin, pervane, şaft ve dümen ölçüsü, zincirin serilmesi, dip
  tapaları) ve havuzdan çıkış kontrolleri: Teekay; Marine Insight; IRClass havuz sörveyi kontrol listesi.
