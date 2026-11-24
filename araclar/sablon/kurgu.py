#!/usr/bin/env python3
"""Shorts kurgusu, Remotion şablonuyla: metin -> Kokoro ses -> kelime zamanlaması -> şablon (araclar/sablon) -> MP4.
Kullanım: python3 -I araclar/sablon/kurgu.py spec.json cikis_klasoru
spec.json make_short.py ile aynıdır: {"voice":"am_michael","blocks":[{"image":"1.jpg","text":"..."},
  {"map":{...},"image":"2.jpg","text":"..."}, ...]}. Harita bloğu araclar/harita bileşeniyle çizilir.
Çıktılar: video.mp4 (tam kalite, ses dahil), rapor.json. Hata olursa sıfırdan farklı kodla çıkar; görev o zaman
make_short.py ile devam eder. Biçim ve kurallar: araclar/sablon/SABLON.md."""
import json, os, re, shutil, subprocess, sys

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(BURASI))            # araclar/ (make_short.py ortak işlevleri)
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
import make_short as ms

FPS = ms.FPS
SATIR = 16            # altyazı satırı en çok karakter (74 px Montserrat ExtraBold, 860 px genişlik)
UNLU = set("aeiouɑɐɒæɛɪɔʊʌəɚɜɝʉɨyøœɘɵɤ")


def agirlik(kelime, k):
    """Kelimenin göreli süresi: fonem sayısı (ünlüler daha uzun) + ardından gelen noktalama duraklaması."""
    cekirdek = re.sub(r"[^\w'’-]", "", kelime)
    ph = k.tokenizer.phonemize(cekirdek, "en-us") if cekirdek else ""
    w = 0.8
    for ch in ph:
        if ch in "ˈˌ":
            continue
        if ch == "ː":
            w += 0.5
        elif ch in UNLU:
            w += 1.5
        elif ch.isspace() or ch == "-":
            w += 0.3
        else:
            w += 1.0
    if kelime.endswith((",", ";", ":")):
        w += 3.0
    elif kelime.endswith((".", "!", "?")):
        w += 1.5
    return w


def bosluklar(ses, sr):
    """Cümle sesindeki duraklamaların ortası (sn): 20 ms pencerede enerji eşiğin altında, en az 120 ms."""
    fr = int(0.02 * sr)
    if len(ses) < 2 * fr:
        return []
    e = np.sqrt(np.mean(ses[: len(ses) // fr * fr].reshape(-1, fr) ** 2, axis=1))
    sessiz, out, i = e < 0.012, [], 0
    while i < len(sessiz):
        if sessiz[i]:
            j = i
            while j < len(sessiz) and sessiz[j]:
                j += 1
            if (j - i) * 0.02 >= 0.12:
                out.append((i + j) / 2 * 0.02)
            i = j
        else:
            i += 1
    return out


def kelime_zamanlari(cumle, t0, sure, k, ses=None, sr=24000):
    """Kelime başına başlangıç/bitiş (sn). Süre fonem ağırlığıyla paylaştırılır; cümle içindeki noktalamalar
    sesteki gerçek duraklamaya (±0,45 sn içindeyse) sabitlenir ve aradaki kelimeler yeniden paylaştırılır."""
    kelimeler = cumle.split()
    ag = [agirlik(x, k) for x in kelimeler]
    top = sum(ag) or 1.0
    cum = np.cumsum([0.0] + ag)
    capa = {0: 0.0, len(kelimeler): sure}             # kelime sınırı indeksi -> zaman
    gaps = bosluklar(ses, sr) if ses is not None else []
    for i, x in enumerate(kelimeler[:-1]):
        if x.endswith((",", ";", ":", ".", "!", "?")) and gaps:
            tahmin = sure * cum[i + 1] / top
            g = min(gaps, key=lambda v: abs(v - tahmin))
            if abs(g - tahmin) <= 0.45:
                capa[i + 1] = g
    sinir = [0.0] * (len(kelimeler) + 1)
    noktalar = sorted(capa)
    for a, b in zip(noktalar, noktalar[1:]):
        ta, tb, wa, wb = capa[a], capa[b], cum[a], cum[b]
        for j in range(a, b + 1):
            sinir[j] = ta + (tb - ta) * ((cum[j] - wa) / (wb - wa) if wb > wa else 0)
    return [{"t": x, "s": t0 + sinir[i], "e": t0 + sinir[i + 1]} for i, x in enumerate(kelimeler)]


def parcalar(kelimeler):
    """Kelimeleri en çok iki satırlık altyazı parçalarına böler; cümle sonunda ve uygun virgülde parça kapanır."""
    out, cur = [], [[]]

    def kapat():
        nonlocal cur
        if cur[0]:
            out.append([line for line in cur if line])
        cur = [[]]

    for w in kelimeler:
        line = cur[-1]
        uzunluk = len(" ".join(x["t"] for x in line + [w]))
        if line and uzunluk > SATIR:
            if len(cur) == 2:
                kapat()
            else:
                cur.append([])
        cur[-1].append(w)
        say = sum(len(l) for l in cur)
        if w["t"].endswith((".", "!", "?")) or (w["t"].endswith((",", ";", ":")) and say >= 3):
            kapat()
    kapat()
    return out


def main(spec_path, out_dir):
    spec = json.load(open(spec_path)); os.makedirs(out_dir, exist_ok=True)
    base = os.path.dirname(os.path.abspath(spec_path))
    pub = os.path.join(out_dir, "public")
    shutil.rmtree(pub, ignore_errors=True)
    shutil.copytree(os.path.join(BURASI, "public"), pub)
    k = Kokoro(ms.MODEL, ms.VOICES)
    voice = spec.get("voice", "am_michael")

    # ses ve kelime zamanları (make_short.py ile aynı aralıklar)
    audio, t, kelimeler, block_starts = [np.zeros(int(ms.LEAD * ms.SR), dtype=np.float32)], ms.LEAD, [], []
    for b in spec["blocks"]:
        block_starts.append(t)
        for s in ms.sentences(b["text"]):
            a, _ = k.create(s, voice=voice, speed=float(spec.get("speed", 1.0)), lang="en-us")
            a = ms.trim(a).astype(np.float32); d = len(a) / ms.SR
            kelimeler += kelime_zamanlari(s, t, d, k, a, ms.SR)
            audio.append(a); t += d
            audio.append(np.zeros(int(ms.GAP_SENT * ms.SR), dtype=np.float32)); t += ms.GAP_SENT
        extra = ms.GAP_BLOCK - ms.GAP_SENT
        audio.append(np.zeros(int(extra * ms.SR), dtype=np.float32)); t += extra
    audio.append(np.zeros(int(ms.TAIL * ms.SR), dtype=np.float32)); total = t + ms.TAIL
    ham = os.path.join(out_dir, "ses_ham.wav"); sf.write(ham, np.concatenate(audio), ms.SR)
    ms.ses_duzeyi(ham, os.path.join(pub, "ses.wav"))

    # bölümler
    bounds = [0.0] + [max(0.0, x - 0.12) for x in block_starts[1:]] + [total]
    frames = round(total * FPS)
    bloklar, harita = [], []
    for i, b in enumerate(spec["blocks"]):
        st, en = round(bounds[i] * FPS), round(bounds[i + 1] * FPS)
        if b.get("map"):
            bloklar.append({"kind": "map", "start": st, "end": en, "map": b["map"]})
            harita.append({"blok": i + 1, "durum": "harita"})
        else:
            ad = f"gorsel{i + 1}{os.path.splitext(b['image'])[1].lower() or '.jpg'}"
            shutil.copyfile(os.path.join(base, b["image"]), os.path.join(pub, ad))
            bloklar.append({"kind": "image", "start": st, "end": en, "src": ad})

    # altyazı parçaları (kare cinsinden)
    chunks = []
    for p in parcalar(kelimeler):
        ws = [w for line in p for w in line]
        chunks.append({"start": round(ws[0]["s"] * FPS), "end": round(ws[-1]["e"] * FPS),
                       "lines": [[{"t": w["t"], "s": round(w["s"] * FPS), "e": round(w["e"] * FPS)} for w in line]
                                 for line in p]})
    for a, b in zip(chunks, chunks[1:]):   # parçalar arası kısa boşlukta yazı ekranda kalsın
        if b["start"] - a["end"] <= round(0.6 * FPS):
            a["end"] = b["start"]
        else:
            a["end"] += round(0.25 * FPS)
    if chunks:
        chunks[-1]["end"] = min(frames, chunks[-1]["end"] + round(0.4 * FPS))

    props = {"frames": frames, "blocks": bloklar, "chunks": chunks, "audio": "ses.wav"}
    pj = os.path.abspath(os.path.join(out_dir, "sablon.json")); json.dump(props, open(pj, "w"), ensure_ascii=False)

    if not os.path.isdir(os.path.join(BURASI, "node_modules")):
        subprocess.run(["npm", "ci", "--no-audit", "--no-fund", "--loglevel=error"], cwd=BURASI, check=True)
    if len(sys.argv) > 4 and sys.argv[3] == "--still":   # yalnız önizleme kareleri
        for fr in sys.argv[4].split(","):
            subprocess.run(["node", "render.mjs", pj, os.path.abspath(os.path.join(out_dir, f"kare-{fr}.png")),
                            os.path.abspath(pub), "--still", fr], cwd=BURASI, check=True)
        return
    ham_v = os.path.abspath(os.path.join(out_dir, "video_ham.mp4"))
    r = subprocess.run(["node", "render.mjs", pj, ham_v, os.path.abspath(pub)], cwd=BURASI,
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.isfile(ham_v):
        sys.exit("şablon üretilemedi: " + (r.stderr or r.stdout)[-800:])
    out = os.path.join(out_dir, "video.mp4"); gecici = os.path.join(out_dir, "video.yarim.mp4")
    # Remotion JPEG karelerden tam aralıklı (yuvj420p) yazar; YouTube için standart aralığa (yuv420p) çevrilir.
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", ham_v, "-vf", "scale=out_range=tv,format=yuv420p",
                    "-c:v", "libx264", "-crf", str(spec.get("crf", 18)), "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-color_range", "tv", "-c:a", "copy", "-movflags", "+faststart", gecici], check=True)
    os.replace(gecici, out)
    rapor = {"video": out, "sablon": "remotion", "sure_sn": round(total, 1), "boyut_mb": round(os.path.getsize(out) / 1e6, 2),
             "altyazi_sayisi": len(chunks), "kelime_sayisi": len(kelimeler),
             "bolum_sinirlari": [round(x, 1) for x in bounds]}
    if harita:
        rapor["harita"] = harita
    if spec.get("parca_mb"):
        rapor["kopru"] = ms.split_file(out, spec["parca_mb"], out_dir)
    json.dump(rapor, open(os.path.join(out_dir, "rapor.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rapor, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
