"""Bir referans videonun yapısını çıkarır: kesmeler, ritim, konuşma metni.

    .referans/venv/bin/python .claude/skills/referans-analiz/analiz.py VIDEO_YA_DA_BAĞLANTI --cikti raporlar/ref

Çıktı: <ad>_analiz.md (promptlara yapıştırılabilir rapor) ve <ad>_analiz.json. Her adım ayrı çalışır;
biri başarısız olursa rapor "Sorunlar" başlığında bunu yazar ve kalan adımlar sürer."""
import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path


def zaman(s):
    s = float(s)
    return f"{int(s // 60)}:{s % 60:04.1f}"


def indir(url, klasor):
    import yt_dlp
    ayar = {"outtmpl": str(klasor / "%(id)s.%(ext)s"), "format": "bv*[height<=720]+ba/b[height<=720]/b",
            "merge_output_format": "mp4", "quiet": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(ayar) as y:
        bilgi = y.extract_info(url, download=True)
        yol = Path(y.prepare_filename(bilgi)).with_suffix(".mp4")
    return yol, {"baslik": bilgi.get("title"), "kanal": bilgi.get("uploader"), "izlenme": bilgi.get("view_count")}


def olc(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                        "-of", "json", str(video)], capture_output=True, text=True, check=True)
    j = json.loads(r.stdout)
    v = next((s for s in j["streams"] if s.get("codec_type") == "video"), {})
    return {"sure": float(j["format"]["duration"]), "genislik": v.get("width"), "yukseklik": v.get("height"), "fps": v.get("r_frame_rate")}


def kesmeler(video):
    from scenedetect import ContentDetector, detect
    return [(a.get_seconds(), b.get_seconds()) for a, b in detect(str(video), ContentDetector())]


def ritim(wav):
    import librosa
    import numpy as np
    y, sr = librosa.load(str(wav), sr=22050, mono=True)
    tempo, kareler = librosa.beat.beat_track(y=y, sr=sr)
    return float(np.atleast_1d(tempo)[0]), [float(t) for t in librosa.frames_to_time(kareler, sr=sr)]


def metin(wav, dil, model):
    from faster_whisper import WhisperModel
    m = WhisperModel(model, device="cpu", compute_type="int8")
    parcalar, bilgi = m.transcribe(str(wav), language=dil or None)
    return bilgi.language, [{"baslangic": p.start, "bitis": p.end, "metin": p.text.strip()} for p in parcalar]


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("kaynak", help="video dosyası ya da bağlantı")
    p.add_argument("--cikti", default="raporlar/referans", help="çıktı klasörü")
    p.add_argument("--dil", default="", help="konuşma dili, ör. tr ya da en (boş: otomatik)")
    p.add_argument("--model", default="small", help="whisper modeli: tiny, base, small, medium, large-v3")
    p.add_argument("--metinsiz", action="store_true", help="konuşmayı yazıya dökme")
    p.add_argument("--ses-ayir", action="store_true", help="demucs ile sesi müzikten ayır (kur.sh --demucs gerekir)")
    a = p.parse_args()

    cikti = Path(a.cikti).resolve()
    cikti.mkdir(parents=True, exist_ok=True)
    sorunlar, veri = [], {"kaynak": a.kaynak}

    if a.kaynak.startswith(("http://", "https://")):
        try:
            video, veri["yayin"] = indir(a.kaynak, cikti)
        except Exception as e:  # noqa: BLE001
            sys.exit(f"İndirilemedi: {e}")
    else:
        video = Path(a.kaynak).resolve()
        if not video.is_file():
            sys.exit(f"Dosya yok: {video}")
    ad = video.stem
    veri["olcu"] = olc(video)
    sure = veri["olcu"]["sure"]

    wav = cikti / f"{ad}.wav"
    ses_var = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "22050", str(wav)]).returncode == 0 and wav.is_file()
    if not ses_var:
        sorunlar.append("Ses çıkarılamadı (videoda ses olmayabilir); ritim ve metin atlandı.")

    try:
        sahne = kesmeler(video) or [(0.0, sure)]
    except Exception as e:  # noqa: BLE001
        sahne, _ = [], sorunlar.append(f"Kesmeler bulunamadı: {e}")
    veri["sahneler"] = [{"baslangic": s, "bitis": b, "sure": b - s} for s, b in sahne]

    tempo, vuruslar = None, []
    if ses_var:
        try:
            tempo, vuruslar = ritim(wav)
        except Exception as e:  # noqa: BLE001
            sorunlar.append(f"Ritim ölçülemedi: {e}")
    veri["tempo_bpm"], veri["vurus_sayisi"] = tempo, len(vuruslar)

    veri["metin"], veri["dil"] = [], None
    if ses_var and not a.metinsiz:
        try:
            veri["dil"], veri["metin"] = metin(wav, a.dil, a.model)
        except Exception as e:  # noqa: BLE001
            sorunlar.append(f"Konuşma yazıya dökülemedi: {e}")

    if a.ses_ayir and ses_var:
        r = subprocess.run([sys.executable, "-m", "demucs", "--two-stems", "vocals", "-o", str(cikti / "ayrik"), str(wav)],
                           capture_output=True, text=True)
        if r.returncode == 0:
            veri["ayrik_ses"] = str(cikti / "ayrik")
        else:
            sorunlar.append("Ses ayrılamadı: " + (r.stderr.strip().splitlines() or ["demucs kurulu değil"])[-1])

    # özet ölçüler
    sureler = [s["sure"] for s in veri["sahneler"]]
    ozet = {}
    if sureler:
        ozet["plan_sayisi"] = len(sureler)
        ozet["ortalama_plan_sn"] = round(statistics.mean(sureler), 2)
        ozet["ortanca_plan_sn"] = round(statistics.median(sureler), 2)
        ozet["ilk_30sn_plan_sayisi"] = sum(1 for s in veri["sahneler"] if s["baslangic"] < 30)
    kesme_anlari = [s["baslangic"] for s in veri["sahneler"][1:]]
    if kesme_anlari and vuruslar:
        isabet = sum(1 for k in kesme_anlari if min(abs(k - v) for v in vuruslar) <= 0.1)
        ozet["vurusa_denk_kesme_orani"] = round(isabet / len(kesme_anlari), 2)
    kelime = sum(len(m["metin"].split()) for m in veri["metin"])
    if kelime:
        ozet["kelime_sayisi"] = kelime
        ozet["dakikada_kelime"] = round(kelime / (sure / 60))
    veri["ozet"], veri["sorunlar"] = ozet, sorunlar

    o = veri["olcu"]
    md = [f"# Referans analizi: {(veri.get('yayin') or {}).get('baslik') or ad}", "",
          f"- Süre: {zaman(sure)} · {o['genislik']}×{o['yukseklik']} · {o['fps']} fps"]
    if veri.get("yayin"):
        md.append(f"- Kanal: {veri['yayin'].get('kanal')} · İzlenme: {veri['yayin'].get('izlenme')}")
    if sureler:
        md.append(f"- Plan sayısı: {ozet['plan_sayisi']} · ortalama {ozet['ortalama_plan_sn']} sn · ortanca {ozet['ortanca_plan_sn']} sn · ilk 30 saniyede {ozet['ilk_30sn_plan_sayisi']} plan")
    if tempo:
        md.append(f"- Tempo: yaklaşık {tempo:.0f} BPM" + (f" · kesmelerin %{ozet['vurusa_denk_kesme_orani'] * 100:.0f}'i vuruşa denk (±0,1 sn)" if "vurusa_denk_kesme_orani" in ozet else ""))
    if kelime:
        md.append(f"- Konuşma: {kelime} kelime · dakikada {ozet['dakikada_kelime']} kelime · dil: {veri['dil']}")
    if veri["metin"]:
        md += ["", "## Kanca (ilk 30 saniye)", "", " ".join(m["metin"] for m in veri["metin"] if m["baslangic"] < 30) or "(konuşma yok)"]
    if sureler:
        md += ["", "## Planlar", "", "| # | Başlangıç | Süre (sn) |", "|---|---|---|"]
        md += [f"| {i} | {zaman(s['baslangic'])} | {s['sure']:.1f} |" for i, s in enumerate(veri["sahneler"], 1)]
    if veri["metin"]:
        md += ["", "## Konuşma metni", ""] + [f"- `{zaman(m['baslangic'])}` {m['metin']}" for m in veri["metin"]]
    if sorunlar:
        md += ["", "## Sorunlar", ""] + [f"- {s}" for s in sorunlar]
    (cikti / f"{ad}_analiz.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (cikti / f"{ad}_analiz.json").write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")
    print(cikti / f"{ad}_analiz.md")
    for s in sorunlar:
        print("uyarı:", s, file=sys.stderr)


if __name__ == "__main__":
    main()
