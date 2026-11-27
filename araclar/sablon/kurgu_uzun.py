#!/usr/bin/env python3
"""Uzun video kurgusu (yatay 1920×1080), Remotion şablonuyla: metin -> Kokoro ses -> kelime zamanlaması ->
şablon (src/uzun) parça parça üretilir -> parçalar kodlanır ve birleştirilir -> MP4.
Kullanım: python3 -I araclar/sablon/kurgu_uzun.py spec.json cikis_klasoru [--still 0,900,…] [--yalniz-ses]
Biçim, bölüm türleri ve ölçümler: araclar/sablon/UZUN.md.

Yarıda kesilen iş aynı komutla kaldığı yerden sürer: cümle sesleri, ham parçalar ve kodlanmış parçalar çıkış
klasöründe saklanır; spec değişince (şablon girdisi değişir) parçalar yeniden üretilir.
Çıktılar: video.mp4 (tam kalite, ses dahil), rapor.json (süreler, boyut, bölüm işaretleri), sablon.json.
İsteğe bağlı spec alanları: "kodlayici" ("x264" varsayılan, "x265"), "crf", "preset"; "parca_mb" (ana kopyayı aktarım
için baytları değiştirmeden böler; video-parca-NN.bin ve video-parcalar.json), "onizleme" (true ise 720p izleme
kopyası: onizleme.mp4; yayınlanmaz)."""
import hashlib, json, os, shutil, subprocess, sys, time

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
sys.path.insert(0, os.path.dirname(BURASI))            # araclar/ (make_short.py ortak işlevleri)
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
import make_short as ms
import kurgu as kg

FPS = ms.FPS
SATIR = 34            # altyazı satırı en çok karakter (50 px Montserrat ExtraBold, yatay kare)
GAP_SENT, GAP_BLOCK, GAP_SEC, LEAD, TAIL = 0.26, 0.5, 0.9, 0.4, 0.8
KART_SN = 2.6         # bölüm ve seri kartının sessiz süresi (sn)
KART_TASMA = 10       # kartın seslendirmenin başına taşan karesi (yumuşak çıkış)
BITIS_SN = 6.0        # bitiş kartının seslendirme bittikten sonra ekranda kaldığı süre (sn)
PARCA_KARE = 900      # bir parçanın kare sayısı (30 sn); küçük parça = yarıda kalırsa az kayıp
NOT_ETIKET = "FROM THE SHIPYARD FLOOR"


def ozet(nesne):
    return hashlib.sha256(json.dumps(nesne, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def calistir(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)


def ses_uret(k, cumle, voice, speed, onbellek):
    """Cümlenin sesini üretir; aynı cümle daha önce üretildiyse diskteki kopyayı kullanır."""
    ad = os.path.join(onbellek, ozet([voice, speed, cumle])[:24] + ".npy")
    if os.path.isfile(ad):
        return np.load(ad)
    a, _ = k.create(cumle, voice=voice, speed=speed, lang="en-us")
    a = ms.trim(a).astype(np.float32)
    np.save(ad + ".yarim.npy", a); os.replace(ad + ".yarim.npy", ad)
    return a


def _uz(ws):
    return len(" ".join(w["t"] for w in ws))


def _bol(ws, n, sinir):
    """Kelimeleri sırayı bozmadan n parçaya böler: parçalar olabildiğince eşit, kesim tercihen noktalamadan sonra.
    Hiçbir parça sinir karakteri aşmamalı; aşıyorsa None döner."""
    if n == 1:
        return [ws] if _uz(ws) <= sinir else None
    hedef, en_iyi = _uz(ws) / n, None
    for i in range(1, len(ws) - n + 2):
        bas = ws[:i]
        if _uz(bas) > sinir:
            break
        kalan = _bol(ws[i:], n - 1, sinir)
        if kalan is None:
            continue
        ceza = sum(abs(_uz(p) - hedef) for p in [bas] + kalan)
        ceza -= 14 * sum(1 for p in ([bas] + kalan)[:-1] if p[-1]["t"].endswith((",", ";", ":")))
        ceza += 8 * sum(1 for p in [bas] + kalan if len(p) == 1)          # tek kelimelik parça kötü durur
        if en_iyi is None or ceza < en_iyi[0]:
            en_iyi = (ceza, [bas] + kalan)
    return en_iyi[1] if en_iyi else None


def parcalar_uzun(kelimeler):
    """Altyazı parçaları (yatay kare): her cümle, en çok iki satırlık (satır başına SATIR karakter) dengeli parçalara
    bölünür; iki satırlı parçanın satırları da dengelenir. Cümle sonunda parça kapanır."""
    out, cumle = [], []
    for w in kelimeler:
        cumle.append(w)
        if w["t"].endswith((".", "!", "?")):
            out += _cumle_parcalari(cumle); cumle = []
    if cumle:
        out += _cumle_parcalari(cumle)
    return out


def _cumle_parcalari(ws):
    n = max(1, -(-_uz(ws) // (2 * SATIR - 6)))
    while True:
        bolum = _bol(ws, n, 2 * SATIR)
        if bolum and all(_satirlar(p) for p in bolum):
            return [_satirlar(p) for p in bolum]
        n += 1
        if n > len(ws):
            return [[[w]] for w in ws]


def _satirlar(ws):
    if _uz(ws) <= SATIR:
        return [ws]
    return _bol(ws, 2, SATIR)


def main(spec_path, out_dir, secenek):
    t_bas = time.time()
    spec = json.load(open(spec_path)); os.makedirs(out_dir, exist_ok=True)
    base = os.path.dirname(os.path.abspath(spec_path))
    pub = os.path.join(out_dir, "public"); onbellek = os.path.join(out_dir, "ses_onbellek")
    os.makedirs(onbellek, exist_ok=True)
    shutil.rmtree(pub, ignore_errors=True)
    shutil.copytree(os.path.join(BURASI, "public"), pub)
    voice, speed = spec.get("voice", "am_michael"), float(spec.get("speed", 1.0))
    _, _, etiket, uyari = ms.ust_yazilar({"label": spec.get("label")})
    seri = spec.get("series") or {}

    # --- ses ve zaman çizgisi ---------------------------------------------------------------------------------
    t0 = time.time()
    k = Kokoro(ms.MODEL, ms.VOICES)
    audio, t = [np.zeros(int(LEAD * ms.SR), dtype=np.float32)], LEAD
    bloklar, kelimeler, kartlar, notlar, isaretler, gorseller = [], [], [], [], [], {}
    sira = 0                                            # başlıklı bölümlerin sırası (PART n)

    def sus(sn):
        nonlocal t
        audio.append(np.zeros(int(sn * ms.SR), dtype=np.float32)); t += sn

    bolumler = spec["sections"]
    for bi, bolum in enumerate(bolumler):
        tur, b_bas = bolum.get("kind", "section"), t
        kart = None
        if bolum.get("card") == "series":
            kart = {"kind": "series", "tag": seri.get("tag"), "name": seri.get("name", "IN THE DRY DOCK"),
                    "title": spec.get("title")}
        elif bolum.get("title") and tur != "note":
            sira += 1
            kart = {"kind": "section", "kicker": bolum.get("kicker", f"PART {sira}"), "title": bolum["title"]}
        if kart:
            kart["start"] = round(t * FPS)
            sus(KART_SN)
            kart["end"] = round(t * FPS) + KART_TASMA
            kartlar.append(kart)
        if bolum.get("chapter") or bolum.get("title"):
            isaretler.append({"sn": round(b_bas, 1), "ad": bolum.get("chapter") or bolum["title"]})
        for ji, b in enumerate(bolum["blocks"]):
            blok = {"t": b_bas if ji == 0 else t, "image": b["image"], "bolum": bi}
            if b.get("move"):
                blok["move"] = b["move"]
            k_bas = len(kelimeler)
            for s in ms.sentences(b["text"]):
                a = ses_uret(k, s, voice, speed, onbellek); d = len(a) / ms.SR
                ws = kg.kelime_zamanlari(s, t, d, k, a, ms.SR)
                if tur == "note":
                    for w in ws:
                        w["note"] = True
                kelimeler += ws
                audio.append(a); t += d
                sus(GAP_SENT)
            sus(GAP_BLOCK - GAP_SENT)
            if b.get("stat"):
                blok["stat"] = {"value": str(b["stat"]["value"]), "label": b["stat"].get("label"),
                                "t0": kelimeler[k_bas]["s"] + 0.5, "t1": t - 0.35}
            if bolum.get("end") and ji == len(bolum["blocks"]) - 1:
                blok["bitis"] = dict(bolum["end"])
            bloklar.append(blok)
        if tur == "note":
            notlar.append({"start": round(b_bas * FPS), "end": round((t - 0.1) * FPS),
                           "label": bolum.get("label", NOT_ETIKET), "by": bolum.get("by")})
        sus(GAP_SEC - GAP_BLOCK)
    if any(b.get("bitis") for b in bloklar):
        sus(BITIS_SN)
    sus(TAIL)
    total = t; frames = round(total * FPS)
    ham = os.path.join(out_dir, "ses_ham.wav"); sf.write(ham, np.concatenate(audio), ms.SR)
    wav = os.path.join(out_dir, "ses.wav"); ms.ses_duzeyi(ham, wav)
    sn_ses = time.time() - t0
    if "--yalniz-ses" in secenek:
        print(json.dumps({"sure_sn": round(total, 1), "kelime_sayisi": len(kelimeler), "ses_sn": round(sn_ses, 1)}))
        return

    # --- şablon girdisi ---------------------------------------------------------------------------------------
    sinir = [0.0] + [max(0.0, b["t"] - 0.15) for b in bloklar[1:]] + [total]
    p_blok = []
    for i, b in enumerate(bloklar):
        if b["image"] not in gorseller:
            ad = f"g{len(gorseller) + 1:03d}{os.path.splitext(b['image'])[1].lower() or '.jpg'}"
            shutil.copyfile(os.path.join(base, b["image"]), os.path.join(pub, ad)); gorseller[b["image"]] = ad
        pb = {"start": round(sinir[i] * FPS), "end": round(sinir[i + 1] * FPS), "src": gorseller[b["image"]]}
        if b.get("move"):
            pb["move"] = b["move"]
        if b.get("stat"):
            pb["stat"] = {"value": b["stat"]["value"], "label": b["stat"]["label"],
                          "start": round(b["stat"]["t0"] * FPS), "end": round(b["stat"]["t1"] * FPS)}
        if b.get("bitis"):
            kartlar.append({"kind": "end", "kicker": b["bitis"].get("kicker", "NEXT QUESTION"),
                            "title": b["bitis"].get("title", ""), "start": pb["start"] + 20, "end": frames})
        p_blok.append(pb)
    chunks = []
    for p in parcalar_uzun(kelimeler):
        ws = [w for line in p for w in line]
        c = {"start": round(ws[0]["s"] * FPS), "end": round(ws[-1]["e"] * FPS),
             "lines": [[{"t": w["t"], "s": round(w["s"] * FPS), "e": round(w["e"] * FPS)} for w in line] for line in p]}
        if ws[0].get("note"):
            c["note"] = True
        chunks.append(c)
    for a, b in zip(chunks, chunks[1:]):   # parçalar arası kısa boşlukta yazı ekranda kalsın
        if b["start"] - a["end"] <= round(0.6 * FPS):
            a["end"] = b["start"]
        else:
            a["end"] += round(0.25 * FPS)
    if chunks:
        chunks[-1]["end"] = min(frames, chunks[-1]["end"] + round(0.4 * FPS))
    props = {"frames": frames, "blocks": p_blok, "chunks": chunks, "cards": kartlar, "notes": notlar}
    if etiket:
        props["label"] = etiket
    pj = os.path.abspath(os.path.join(out_dir, "sablon.json")); json.dump(props, open(pj, "w"), ensure_ascii=False)

    if not os.path.isdir(os.path.join(BURASI, "node_modules")):
        calistir(["npm", "ci", "--no-audit", "--no-fund", "--loglevel=error"], cwd=BURASI)
    if "--still" in secenek:               # yalnız önizleme kareleri
        kareler = secenek[secenek.index("--still") + 1]
        calistir(["node", "render_uzun.mjs", pj, os.path.abspath(pub), "--still", kareler, os.path.abspath(out_dir)], cwd=BURASI)
        print(json.dumps({"sure_sn": round(total, 1), "kare": frames, "bolum_isaretleri": isaretler}, ensure_ascii=False))
        return

    # --- parçalar: üretim (Remotion) ve kodlama ---------------------------------------------------------------
    kodlayici = spec.get("kodlayici", "x264")
    if kodlayici not in ("x264", "x265"):
        sys.exit("kodlayici yalnız x264 ya da x265 olabilir")
    crf = int(spec.get("crf", 19 if kodlayici == "x265" else 18)); preset = spec.get("preset", "medium")
    if kodlayici == "x265":            # aynı ölçülen kalitede yaklaşık yarı boyut; kodlama yaklaşık 3,5 kat sürer (UZUN.md)
        v_kod = ["-c:v", "libx265", "-crf", str(crf), "-preset", preset, "-x265-params", "log-level=error", "-tag:v", "hvc1"]
    else:                              # Shorts hattıyla aynı ayar (ortamın ffmpeg başlatıcısı için bkz. UZUN.md)
        v_kod = ["-c:v", "libx264", "-crf", str(crf), "-preset", preset]
    p_kare = int(spec.get("parca_kare", PARCA_KARE))
    gorsel_ozet = {v: ms.sha256_file(os.path.join(pub, v)) for v in gorseller.values()}
    kimlik = ozet([props, gorsel_ozet, os.environ.get("UZUN_KARE", "jpeg")])[:12]
    pdir = os.path.join(out_dir, "parcalar", kimlik); os.makedirs(pdir, exist_ok=True)
    parcalar = [{"ad": f"p{i:03d}", "ilk": a, "son": min(frames, a + p_kare) - 1,
                 "cikis": os.path.abspath(os.path.join(pdir, f"p{i:03d}_ham.mp4"))}
                for i, a in enumerate(range(0, frames, p_kare))]
    kdir = os.path.join(pdir, f"kod_{kodlayici}_{crf}_{preset}"); os.makedirs(kdir, exist_ok=True)   # kodlanmış parçalar
    eksik = [p for p in parcalar if not os.path.isfile(os.path.join(kdir, p["ad"] + ".mp4")) and not os.path.isfile(p["cikis"])]
    plist = os.path.join(pdir, "parcalar.json"); json.dump(eksik, open(plist, "w"))
    sn_uretim, parca_sn = 0.0, {}
    if eksik:
        t1 = time.time()
        with open(os.path.join(out_dir, "uretim.log"), "a") as log:
            pr = subprocess.Popen(["node", "render_uzun.mjs", pj, os.path.abspath(pub), "--parcalar", os.path.abspath(plist)],
                                  cwd=BURASI, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for satir in pr.stdout:
                log.write(satir); log.flush()
                try:
                    j = json.loads(satir)
                    if j.get("asama") == "parca" and "sn" in j:
                        parca_sn[j["ad"]] = round(j["sn"], 1)
                except ValueError:
                    pass
            if pr.wait() != 0:
                sys.exit("şablon üretilemedi; ayrıntı: " + os.path.join(out_dir, "uretim.log"))
        sn_uretim = time.time() - t1
    t2 = time.time()
    for p in parcalar:                      # Remotion tam aralıklı (yuvj420p) yazar; standart aralığa çevrilir
        son = os.path.join(kdir, p["ad"] + ".mp4")
        if os.path.isfile(son):
            continue
        gecici = son[:-4] + ".yarim.mp4"
        calistir(["ffmpeg", "-y", "-loglevel", "error", "-i", p["cikis"], "-vf", "scale=out_range=tv,format=yuv420p"]
                 + v_kod + ["-pix_fmt", "yuv420p", "-color_range", "tv", "-an", gecici])
        os.replace(gecici, son)
        if not os.environ.get("UZUN_HAM_SAKLA"):
            os.remove(p["cikis"])           # ham parça büyüktür; kodlanınca silinir (ölçüm için saklanabilir)
    sn_kodlama = time.time() - t2

    # --- birleştirme ------------------------------------------------------------------------------------------
    t3 = time.time()
    lst = os.path.join(kdir, "liste.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(os.path.join(kdir, p['ad'] + '.mp4'))}'\n" for p in parcalar))
    out = os.path.join(out_dir, "video.mp4"); gecici = os.path.join(out_dir, "video.yarim.mp4")
    calistir(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav, "-map", "0:v", "-map", "1:a",
              "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-t", f"{total:.3f}", gecici])
    os.replace(gecici, out)
    sn_birlestirme = time.time() - t3
    boyut = os.path.getsize(out)
    rapor = {"video": out, "sablon": "remotion-uzun", "sure_sn": round(total, 1), "kare": frames,
             "kodlama": f"{kodlayici} crf {crf} {preset}", "boyut_mb": round(boyut / 1e6, 2), "boyut_mib": round(boyut / 2**20, 2),
             "bit_hizi_mbit": round(boyut * 8 / total / 1e6, 2), "sha256": ms.sha256_file(out),
             "kelime_sayisi": len(kelimeler), "altyazi_sayisi": len(chunks), "blok_sayisi": len(p_blok),
             "gorsel_sayisi": len(gorseller), "parca_sayisi": len(parcalar), "bu_calismada_uretilen_parca": len(eksik),
             "sn": {"ses": round(sn_ses, 1), "uretim": round(sn_uretim, 1), "kodlama": round(sn_kodlama, 1),
                    "birlestirme": round(sn_birlestirme, 1), "toplam": round(time.time() - t_bas, 1)},
             "parca_uretim_sn": parca_sn, "bolum_isaretleri": isaretler}
    if etiket:
        rapor["etiket"] = etiket
    if uyari:
        rapor["uyarilar"] = uyari
    if spec.get("parca_mb"):                # aktarım: ana kopya baytları değişmeden bölünür
        rapor["aktarim"] = ms.split_file(out, spec["parca_mb"], out_dir)
        json.dump(rapor["aktarim"], open(os.path.join(out_dir, "video-parcalar.json"), "w"), indent=1)
    if spec.get("onizleme"):                # onay için izleme kopyası (yayınlanmaz): 720p H.264
        t4 = time.time(); prev = os.path.join(out_dir, "onizleme.mp4")
        calistir(["ffmpeg", "-y", "-loglevel", "error", "-i", out, "-vf", "scale=-2:720", "-c:v", "libx264", "-crf", "27",
                  "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ac", "1", "-b:a", "64k",
                  "-movflags", "+faststart", prev])
        rapor["onizleme"] = {"dosya": prev, "boyut_mb": round(os.path.getsize(prev) / 1e6, 2), "sn": round(time.time() - t4, 1)}
    rapor["sn"]["toplam"] = round(time.time() - t_bas, 1)
    json.dump(rapor, open(os.path.join(out_dir, "rapor.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rapor, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
