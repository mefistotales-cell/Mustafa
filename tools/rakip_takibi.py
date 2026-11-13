"""Rakip kanalların son videolarını tarar ve kanal ortalamasının çok üstünde izlenenleri bulur.

Kullanım: python3 -m tools.rakip_takibi @kanal1 @kanal2 [--adet 50] [--esik 2] [--shorts-haric] [--cikti rapor.md]
"""
import argparse

from . import yt


def outliers(videos, threshold=2.0):
    """Günlük izlenmesi kanal ortancasının `threshold` katını aşan videoları döndürür.

    Her kayıt (video, kat) ikilisidir; en yüksek kattan düşüğe sıralıdır.
    """
    med = yt.median(yt.views_per_day(v) for v in videos)
    if not med:
        return []
    scored = [(v, yt.views_per_day(v) / med) for v in videos]
    return sorted([s for s in scored if s[1] >= threshold], key=lambda s: s[1], reverse=True)


def report(channels, threshold):
    out = ["# Rakip kanal takibi", ""]
    summary, sections = [], []
    for ch, videos in channels:
        name = ch["snippet"]["title"]
        subs = ch.get("statistics", {}).get("subscriberCount")
        summary.append([name, yt.fmt(int(subs)) if subs else "gizli", len(videos),
                        yt.fmt(yt.median(v["views"] for v in videos))])
        hits = outliers(videos, threshold)
        sections += [f"## {name}", ""]
        if hits:
            sections.append(yt.md_table(["Kat", "İzlenme", "Yayın", "Başlık"],
                                        [[f"{k:.1f}x", yt.fmt(v["views"]), v["published"].date(), v["title"]]
                                         for v, k in hits[:10]]))
        else:
            sections.append("Eşiği aşan video yok.")
        sections.append("")
    out.append(yt.md_table(["Kanal", "Abone", "Video", "Ortanca izlenme"], summary))
    out += ["", f"Aşağıdaki videoların günlük izlenmesi, kendi kanalının ortancasının en az {threshold:g} katı.", ""]
    return "\n".join(out + sections).rstrip()


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("kanallar", nargs="+", help="@kullanıcıadı, kanal URL'si veya UC... kimliği")
    p.add_argument("--adet", type=int, default=50, help="kanal başına taranacak son video sayısı")
    p.add_argument("--esik", type=float, default=2.0)
    p.add_argument("--shorts-haric", action="store_true", help="60 saniye ve altındaki videoları sayma")
    p.add_argument("--cikti")
    args = p.parse_args()
    channels = []
    for ref in args.kanallar:
        ch = yt.resolve_channel(ref)
        videos = yt.channel_videos(ch, args.adet)
        if args.shorts_haric:
            videos = [v for v in videos if v["seconds"] > 60]
        channels.append((ch, videos))
    yt.emit(report(channels, args.esik), args.cikti)


if __name__ == "__main__":
    yt.run(main)
