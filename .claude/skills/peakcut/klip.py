"""Bir video dosyasından PeakCut ile dikey, altyazılı klipler üretir.

    .peakcut/venv/bin/python .claude/skills/peakcut/klip.py video.mp4 --cikti klipler/

Sunucu çalışmıyorsa kendisi başlatır, videoyu yükler, iş bitene kadar bekler, klipleri ve
özet JSON'u çıktı klasörüne kopyalar. İş bitince kendi başlattığı sunucuyu kapatır."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import httpx

KOK = Path(__file__).resolve().parents[3]
PC = KOK / ".peakcut"
PORT = int(os.environ.get("PEAKCUT_PORT", "8765"))
BASE = f"http://127.0.0.1:{PORT}"


def ayakta(c):
    try:
        return c.get(BASE + "/healthz", timeout=2).status_code == 200
    except httpx.HTTPError:
        return False


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("video")
    p.add_argument("--cikti", default="klipler", help="kliplerin kopyalanacağı klasör")
    p.add_argument("--adet", type=int, default=6, help="en fazla klip sayısı")
    p.add_argument("--en-kisa", type=int, default=15, help="saniye")
    p.add_argument("--en-uzun", type=int, default=60, help="saniye")
    p.add_argument("--stil", default="bounce", choices=["bounce", "hype", "clean"], help="altyazı stili")
    p.add_argument("--bekle", type=int, default=3600, help="en fazla bekleme süresi, saniye")
    a = p.parse_args()

    video = Path(a.video).resolve()
    if not video.is_file():
        sys.exit(f"Dosya yok: {video}")
    if not (PC / "app").is_dir():
        sys.exit("PeakCut kurulu değil. Önce: bash .claude/skills/peakcut/kur.sh")

    veri = PC / "data"
    c = httpx.Client(trust_env=False, headers={"Origin": BASE})
    sunucu = None
    if not ayakta(c):
        env = {**os.environ, "PEAKCUT_DATA": str(veri), "PEAKCUT_PORT": str(PORT), "PEAKCUT_HOST": "127.0.0.1",
               "PEAKCUT_UPDATE_CHECK": "0", "PEAKCUT_AUTO_RELOAD": "0"}
        veri.mkdir(parents=True, exist_ok=True)
        log = (PC / "sunucu.log").open("w")
        sunucu = subprocess.Popen([sys.executable, "-m", "studio.server"], cwd=PC / "app", env=env,
                                  stdout=log, stderr=subprocess.STDOUT)
        # ilk açılışta yaklaşık 480 MB konuşma modeli iner; bu yüzden uzun bekliyoruz
        for _ in range(900):
            if ayakta(c):
                break
            if sunucu.poll() is not None:
                sys.exit(f"Sunucu başlamadı, bkz. {PC / 'sunucu.log'}")
            time.sleep(1)
        else:
            sunucu.terminate()
            sys.exit("Sunucu 15 dakikada başlamadı.")
    try:
        secenek = {"max_clips": a.adet, "min_len": a.en_kisa, "max_len": a.en_uzun, "style": a.stil}
        with video.open("rb") as f:
            r = c.post(BASE + "/api/upload", files={"file": (video.name, f)},
                       data={"options": json.dumps(secenek)}, timeout=None)
        if r.status_code != 200:
            sys.exit(f"Yükleme reddedildi ({r.status_code}): {r.text[:300]}")
        jid = r.json()["id"]
        son, bitis = "", time.time() + a.bekle
        while True:
            j = c.get(f"{BASE}/api/jobs/{jid}", timeout=30).json()
            durum = f"{j['status']}: {j['stage']}"
            if durum != son:
                print(durum, file=sys.stderr, flush=True)
                son = durum
            if j["status"] in ("done", "error", "failed") or j.get("error"):
                break
            if time.time() > bitis:
                sys.exit(f"Süre doldu; iş hâlâ sürüyor ({jid}).")
            time.sleep(3)
        if j.get("error") or j["status"] != "done":
            sys.exit(f"İş başarısız: {j.get('error') or j['status']}")
        cikti = Path(a.cikti).resolve()
        cikti.mkdir(parents=True, exist_ok=True)
        kaynak = next(veri.glob(f"users/*/jobs/{jid}/clips"), None) if veri.is_dir() else None
        ozet = []
        for k in j["clips"]:
            hedef = None
            if kaynak and k.get("file") and (kaynak / k["file"]).is_file():
                hedef = cikti / f"{video.stem}_{k['file']}"
                shutil.copy2(kaynak / k["file"], hedef)
            ozet.append({"dosya": str(hedef) if hedef else None, "baslangic": k["start"], "bitis": k["end"],
                         "puan": k.get("score"), "kanca": k.get("hook"), "baslik": k.get("title"),
                         "aciklama": k.get("description"), "etiketler": k.get("hashtags"),
                         "neden": k.get("reason"), "durum": k.get("status"), "hata": k.get("error")})
        sonuc = {"is": jid, "sure": j.get("duration"), "kelime": j.get("word_count"),
                 "yapay_zeka": j.get("ai"), "klipler": ozet}
        (cikti / f"{video.stem}_klipler.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    finally:
        if sunucu:
            sunucu.terminate()


if __name__ == "__main__":
    main()
