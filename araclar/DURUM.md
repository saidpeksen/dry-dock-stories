# durum.json

Üretim hattının durumu. Depo kökünde durur; durumu gösteren site bu dosyayı okur.
Kişisel bilgi, belirteç, Drive bağlantısı ya da e-posta yazılmaz. Dosya herkese açıktır.

```json
{
  "schema": 1,
  "updated_at": "2026-11-21T08:30:00Z",
  "channel": "Dry Dock Stories",
  "note": "İsteğe bağlı kısa not (en çok 300 karakter)",
  "runs": {"claude": "2026-11-21T08:30:00Z", "chatgpt": null},
  "videos": [
    {"no": 2, "slug": "02-kisa-ad", "topic": "Konu (yıl)", "title": "YouTube başlığı", "hook": "Açılış cümlesi",
     "stage": "onay", "seconds": 42.3, "video": true, "bytes": 20399520,
     "sha256": "<videonun 64 haneli sha256 özeti>", "youtube_url": null,
     "ordered_at": null, "ready_at": "2026-11-21T08:17:00Z", "approved_at": null, "published_at": null}
  ]
}
```

| stage | Anlamı | Köprüdeki karşılığı |
|---|---|---|
| `siparis` | Görsel bekleniyor | SIPARIS var, görseller eksik |
| `kurgu` | Kurgu bekleniyor | 5 görsel tam, YAYIN-BILGISI yok |
| `onay` | Onay bekliyor | YAYIN-BILGISI var, ONAYLANDI yok |
| `duzeltme` | Düzeltiliyor | Klasörde DUZELT belgesi var, yeni video hazırlanıyor |
| `beklemede` | Bekletiliyor | Bekletilmesi istendi |
| `yayin` | Yayın bekleniyor | ONAYLANDI var, YAYINLANDI.txt yok |
| `yayinda` | Yayında | YAYINLANDI.txt var (`youtube_url` zorunlu) |

- `video`: önizleme videosu depoda `videolar/<slug>/video.mp4` olarak duruyorsa `true`.
- `bytes` ve `sha256`: videonun bayt sayısı ve özeti; YAYIN-BILGISI'ndeki değerlerle aynı. `onay` aşamasında zorunlu:
  sitedeki Onayla / Düzelt / Beklet düğmeleri bu özete bağlanır.
- Tarihler saat dilimli ISO biçiminde; bilinmeyen tarih `null` yazılır, tahmin edilmez.
- `runs.claude`: bu dosyayı yazan çalışmanın saati. `runs.chatgpt`: bilinen son ChatGPT çalışması; bilinmiyorsa `null`.
- Yazdıktan sonra: `python3 -I araclar/durum_denetle.py durum.json`
