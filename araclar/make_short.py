#!/usr/bin/env python3
"""Shorts kurgu hattı: metin -> Kokoro ses -> altyazı (ASS) -> ffmpeg ile 1080x1920 MP4.
Kullanım: python3 -I make_short.py spec.json cikis_klasoru
spec.json: {"voice":"am_michael","parca_mb":2.8,"onizleme_mb":2.9,
            "blocks":[{"image":"1.jpg","text":"..."}, ...]}
Her blok bir görsele karşılık gelir; metin cümlelere bölünüp sırayla seslendirilir.
Harita bloğu: görsel yerine {"map": {...}, "text": "..."}; harita araclar/harita ile (Remotion) çizilir,
biçimi araclar/harita/HARITA.md'de. Blokta "image" de varsa harita üretilemediğinde görsele düşülür.
Çıktılar: video.mp4 (tam kalite ana kopya), video-parca-NN.bin (köprü için bölünmüş ana kopya),
onizleme.mp4 (yalnız onay için izleme kopyası, sıkıştırılmış).
İlk kare başlığı ("headline") ve köşe etiketi ("label") yalnız şablonda (araclar/sablon) çizilir; bu yedek hat
alanları kabul eder, çizmez ve rapor.json'a uyarı yazar."""
import hashlib, json, re, subprocess, sys, os
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

MODEL = "/home/claude/tts/models/kokoro-v1.0.onnx"
VOICES = "/home/claude/tts/models/voices-v1.0.bin"
SR, FPS, W, H = 24000, 30, 1080, 1920
GAP_SENT, GAP_BLOCK, LEAD, TAIL = 0.22, 0.42, 0.30, 0.60
ETIKET = "AI reconstruction"   # "label": true iken yazılan köşe etiketi

def ust_yazilar(spec):
    """İsteğe bağlı alanları okur: "headline" (ilk kare başlığı; 2–4 kelime, büyük harfe çevrilir), "headline_y"
    (başlığın orta yüksekliği, piksel) ve "label" (köşe etiketi; true ise ETIKET, metin verilirse o metin).
    Döner: (başlık | None, y | None, etiket | None, uyarılar). Hata vermez; biçimi bozuk alan yok sayılır ve uyarılır."""
    uyari = []
    h = spec.get("headline")
    if h is not None and not isinstance(h, str):
        uyari.append("headline metin değil; yok sayıldı"); h = None
    h = " ".join(h.split()).upper() if h else None
    if h:
        n = len(h.split())
        if not 2 <= n <= 4:
            uyari.append(f"headline {n} kelime (beklenen 2–4)")
        if len(h) > 40:
            uyari.append(f"headline {len(h)} karakter; küçük yazılır (beklenen en çok 40)")
    y = spec.get("headline_y")
    if y is not None and (isinstance(y, bool) or not isinstance(y, (int, float)) or y != y or abs(y) == float("inf")):
        uyari.append("headline_y sayı değil; yok sayıldı"); y = None
    e = spec.get("label")
    if e is True:
        e = ETIKET
    elif isinstance(e, str):
        e = " ".join(e.split())[:40] or None
    else:
        if e not in (None, False):
            uyari.append("label true ya da metin değil; yok sayıldı")
        e = None
    return h or None, (y if h else None), e, uyari

def trim(x, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    return x[idx[0]:idx[-1] + 1] if len(idx) else x

def sentences(t):
    parts = re.split(r'(?<=[.!?])\s+', t.strip())
    return [p for p in parts if p]

def chunks(sentence, max_chars=17, max_lines=3):
    words, lines, cur = sentence.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur: lines.append(cur)
    return [lines[i:i + max_lines] for i in range(0, len(lines), max_lines)]

def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()

def split_file(path, part_mb, out_dir, stem="video-parca"):
    """Dosyayı sırayla birleştirilince aynı baytları veren parçalara böler."""
    size, part_bytes, parts = os.path.getsize(path), int(float(part_mb) * 1_000_000), []
    with open(path, "rb") as f:
        i = 1
        while True:
            blk = f.read(part_bytes)
            if not blk: break
            p = os.path.join(out_dir, f"{stem}-{i:02d}.bin")
            open(p, "wb").write(blk)
            parts.append({"ad": os.path.basename(p), "bayt": len(blk), "sha256": sha256_file(p)})
            i += 1
    return {"toplam_bayt": size, "sha256": sha256_file(path), "parcalar": parts}

def ses_duzeyi(src, dst, I=-14.0, TP=-1.5, LRA=11.0):
    """Sesi YouTube referans düzeyine yaklaştırır (iki geçişli loudnorm; ham Kokoro çıkışı yaklaşık -23 LUFS)."""
    base = f"loudnorm=I={I}:TP={TP}:LRA={LRA}"
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-af", base + ":print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True, check=True)
    m = json.loads(re.findall(r"\{[^{}]*\}", p.stderr)[-1])
    af = (base + f":measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", af, "-ar", "48000", "-c:a", "pcm_s16le", dst], check=True)


HARITA = os.environ.get("HARITA_DIZINI") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "harita")

def harita_bolumu(harita, frames, seg, out_dir, i):
    """Harita bloğunu Remotion ile üretir (araclar/harita) ve diğer bölümlerle aynı ayarlara getirir."""
    if not os.path.isdir(os.path.join(HARITA, "node_modules")):
        subprocess.run(["npm", "ci", "--no-audit", "--no-fund", "--loglevel=error"], cwd=HARITA, check=True)
    props = dict(harita); props["frames"] = frames
    pj = os.path.abspath(os.path.join(out_dir, f"harita{i}.json")); json.dump(props, open(pj, "w"), ensure_ascii=False)
    ham = os.path.abspath(os.path.join(out_dir, f"harita{i}_ham.mp4"))
    r = subprocess.run(["node", os.path.join(HARITA, "render.mjs"), pj, ham], cwd=HARITA, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.isfile(ham):
        raise RuntimeError("harita üretilemedi: " + (r.stderr or r.stdout)[-600:])
    gecici = seg[:-4] + ".yarim.mp4"   # yarım kalan dosya tam sanılmasın
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", ham, "-vf", f"fps={FPS},scale={W}:{H}:out_range=tv,format=yuv420p",
                    "-frames:v", str(frames), "-c:v", "libx264", "-crf", "12", "-preset", "veryfast",
                    "-pix_fmt", "yuv420p", "-color_range", "tv", gecici], check=True)
    os.replace(gecici, seg)

def main(spec_path, out_dir):
    spec = json.load(open(spec_path)); os.makedirs(out_dir, exist_ok=True)
    base = os.path.dirname(os.path.abspath(spec_path))
    k = Kokoro(MODEL, VOICES)
    voice = spec.get("voice", "am_michael")
    audio, t, events, block_starts = [np.zeros(int(LEAD * SR), dtype=np.float32)], LEAD, [], []
    for b in spec["blocks"]:
        block_starts.append(t)
        for s in sentences(b["text"]):
            a, _ = k.create(s, voice=voice, speed=float(spec.get("speed", 1.0)), lang="en-us")
            a = trim(a).astype(np.float32); d = len(a) / SR
            groups = chunks(s); total = sum(len(" ".join(g)) for g in groups); c = t
            for g in groups:
                gd = d * len(" ".join(g)) / total
                events.append((c, c + gd, "\\N".join(g))); c += gd
            audio.append(a); t += d
            audio.append(np.zeros(int(GAP_SENT * SR), dtype=np.float32)); t += GAP_SENT
        extra = GAP_BLOCK - GAP_SENT
        audio.append(np.zeros(int(extra * SR), dtype=np.float32)); t += extra
    audio.append(np.zeros(int(TAIL * SR), dtype=np.float32)); total_dur = t + TAIL
    ham = os.path.join(out_dir, "ses_ham.wav"); sf.write(ham, np.concatenate(audio), SR)
    wav = os.path.join(out_dir, "ses.wav"); ses_duzeyi(ham, wav)
    # altyazı
    ass = os.path.join(out_dir, "altyazi.ass")
    with open(ass, "w") as f:
        f.write(f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\nWrapStyle: 2\n\n"
                "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
                "Style: D,DejaVu Sans,78,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,2,2,60,60,520,1\n\n"
                "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for s, e, txt in events:
            f.write(f"Dialogue: 0,{ts(s)},{ts(e)},D,,0,0,0,,{txt}\n")
    # görsel bölümleri
    bounds = [0.0] + [max(0.0, x - 0.12) for x in block_starts[1:]] + [total_dur]
    segs, harita_raporu = [], []
    for i, b in enumerate(spec["blocks"]):
        dur = bounds[i + 1] - bounds[i]; frames = max(1, round(dur * FPS))
        seg = os.path.join(out_dir, f"seg{i}.mp4"); segs.append(seg)
        if b.get("map"):
            try:
                harita_bolumu(b["map"], frames, seg, out_dir, i)
                harita_raporu.append({"blok": i + 1, "durum": "harita"})
                continue
            except Exception as e:  # harita üretilemezse varsa görsele düş, yoksa dur
                if not b.get("image"):
                    raise
                harita_raporu.append({"blok": i + 1, "durum": "görsele düşüldü", "hata": str(e)[-300:]})
        z = f"1+0.12*on/{frames}" if i % 2 == 0 else f"1.12-0.12*on/{frames}"
        vf = (f"scale={W*2}:{H*2}:force_original_aspect_ratio=increase,crop={W*2}:{H*2},"
              f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-loop", "1", "-i",
                        os.path.join(base, b["image"]), "-vf", vf, "-frames:v", str(frames), "-c:v", "libx264",
                        "-crf", "12", "-preset", "veryfast", "-pix_fmt", "yuv420p", seg], check=True)
    lst = os.path.join(out_dir, "list.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(s)}'\n" for s in segs))
    # ana kopya: tam kalite H.264
    out = os.path.join(out_dir, "video.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                    "-vf", f"ass={ass}", "-c:v", "libx264", "-crf", str(spec.get("crf", 18)), "-preset", "slow",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
                    "-t", f"{total_dur:.2f}", out], check=True)
    rapor = {"video": out, "sure_sn": round(total_dur, 1), "boyut_mb": round(os.path.getsize(out) / 1e6, 2),
             "altyazi_sayisi": len(events), "bolum_sinirlari": [round(x, 1) for x in bounds]}
    if harita_raporu:
        rapor["harita"] = harita_raporu
    baslik, _, etiket, uyari = ust_yazilar(spec)
    if baslik or etiket:   # yedek hat bunları çizmez; kaydı tutan bilsin
        uyari.append("yedek hat ilk kare başlığını ve köşe etiketini çizmez (yalnız şablonda var)")
    if uyari:
        rapor["uyarilar"] = uyari
    # köprü: ana kopyayı kayıpsız parçalara böl (bağlayıcı çağrısı başına ~3 MB sınırı)
    if spec.get("parca_mb"):
        rapor["kopru"] = split_file(out, spec["parca_mb"], out_dir)
    # onay için izleme kopyası: HEVC, iki geçişli, boyut hedefli (yayınlanmaz)
    if spec.get("onizleme_mb"):
        prev = os.path.join(out_dir, "onizleme.mp4")
        vk = int((float(spec["onizleme_mb"]) * 8000 / total_dur - 56) * 0.97)
        stats = os.path.join(out_dir, "x265.log")
        common = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav,
                  "-vf", f"ass={ass}", "-c:v", "libx265", "-preset", "medium", "-b:v", f"{vk}k", "-pix_fmt", "yuv420p"]
        subprocess.run(common + ["-x265-params", f"pass=1:stats={stats}:log-level=error", "-an", "-t", f"{total_dur:.2f}",
                                 "-f", "null", "/dev/null"], check=True)
        subprocess.run(common + ["-x265-params", f"pass=2:stats={stats}:log-level=error", "-tag:v", "hvc1", "-c:a", "aac",
                                 "-ac", "1", "-b:a", "56k", "-movflags", "+faststart", "-t", f"{total_dur:.2f}", prev], check=True)
        rapor["onizleme"] = {"dosya": prev, "boyut_mb": round(os.path.getsize(prev) / 1e6, 2)}
    json.dump(rapor, open(os.path.join(out_dir, "rapor.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(rapor, ensure_ascii=False))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
