"""Bir kanalın videolarını yayın günü ve saatine göre karşılaştırır.

Kullanım: python3 -m tools.yayin_zamani @kanalim [--adet 100] [--saat-dilimi Europe/Istanbul] [--shorts-haric] [--cikti rapor.md]
"""
import argparse
from collections import defaultdict
from zoneinfo import ZoneInfo

from . import yt

DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
SLOTS = [(0, "00-06"), (6, "06-12"), (12, "12-18"), (18, "18-24")]


def slot(hour):
    return [label for start, label in SLOTS if hour >= start][-1]


def group(videos, tz):
    """Videoları güne ve saat aralığına göre gruplayıp (etiket, adet, ortanca izlenme) listeleri döndürür."""
    by_day, by_slot = defaultdict(list), defaultdict(list)
    for v in videos:
        local = v["published"].astimezone(tz)
        by_day[local.weekday()].append(v["views"])
        by_slot[slot(local.hour)].append(v["views"])
    days = [(DAYS[d], len(by_day[d]), yt.median(by_day[d])) for d in range(7) if by_day[d]]
    slots = [(label, len(by_slot[label]), yt.median(by_slot[label])) for _, label in SLOTS if by_slot[label]]
    return days, slots


def report(name, videos, tz_name):
    days, slots = group(videos, ZoneInfo(tz_name))
    rows = lambda data: [[label, n, yt.fmt(med)] for label, n, med in data]
    out = [f"# Yayın zamanı analizi: {name}", "",
           f"İncelenen video: {len(videos)} (saat dilimi: {tz_name})", "",
           "## Güne göre", "", yt.md_table(["Gün", "Video", "Ortanca izlenme"], rows(days)), "",
           "## Saat aralığına göre", "", yt.md_table(["Saat", "Video", "Ortanca izlenme"], rows(slots)), ""]
    solid = [d for d in days if d[1] >= 3]
    if solid:
        best = max(solid, key=lambda d: d[2])
        out.append(f"En az 3 videosu olan günler içinde en yüksek ortanca: **{best[0]}** ({yt.fmt(best[2])}).")
    else:
        out.append("Hiçbir günde 3 videodan fazla yok; sonuç çıkarmak için veri yetersiz.")
    out.append("Not: eski videolar daha uzun süredir izlenme topladığı için bu tablo yön gösterir, kesin kanıt değildir.")
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("kanal")
    p.add_argument("--adet", type=int, default=100)
    p.add_argument("--saat-dilimi", default="Europe/Istanbul")
    p.add_argument("--shorts-haric", action="store_true")
    p.add_argument("--cikti")
    args = p.parse_args()
    ch = yt.resolve_channel(args.kanal)
    videos = yt.channel_videos(ch, args.adet)
    if args.shorts_haric:
        videos = [v for v in videos if v["seconds"] > 60]
    yt.emit(report(ch["snippet"]["title"], videos, args.saat_dilimi), args.cikti)


if __name__ == "__main__":
    yt.run(main)
