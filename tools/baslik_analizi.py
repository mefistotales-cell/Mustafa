"""Bir arama ifadesinde en çok izlenen videoların başlık ve etiket kalıplarını çıkarır.

Kullanım: python3 -m tools.baslik_analizi "arama ifadesi" [--adet 25] [--bolge TR] [--dil tr] [--cikti rapor.md]
Not: her çalıştırma 100 birim API kotası harcar (günlük ücretsiz kota 10.000).
"""
import argparse
import re
from collections import Counter

from . import yt

STOP = set("""ve ile bir bu şu o da de mi mı mu mü için gibi en çok daha ne nasıl neden ama veya ya
ki her hiç ben sen biz siz var yok olan olarak the a an of to in for and is on how what why with""".split())


def words(title):
    return [w for w in re.findall(r"[^\W\d_]{3,}", title.lower()) if w not in STOP]


def analyze(videos):
    """Başlık kalıplarına dair özet istatistikleri döndürür."""
    n = len(videos) or 1
    titles = [v["title"] for v in videos]
    return {
        "count": len(videos),
        "median_len": yt.median(len(t) for t in titles),
        "pct_number": 100 * sum(bool(re.search(r"\d", t)) for t in titles) / n,
        "pct_question": 100 * sum("?" in t for t in titles) / n,
        "pct_caps": 100 * sum(bool(re.search(r"\b[A-ZÇĞİÖŞÜ]{3,}\b", t)) for t in titles) / n,
        "pct_bracket": 100 * sum(bool(re.search(r"[\[\(]", t)) for t in titles) / n,
        "median_minutes": yt.median(v["seconds"] for v in videos) / 60,
        "top_words": Counter(w for t in titles for w in set(words(t))).most_common(15),
        "top_tags": Counter(tag.lower() for v in videos for tag in set(v["tags"])).most_common(15),
    }


def report(query, videos):
    a = analyze(videos)
    top = sorted(videos, key=lambda v: v["views"], reverse=True)
    out = [f"# Başlık analizi: \"{query}\"", "", f"İncelenen video: {a['count']}", ""]
    out.append(yt.md_table(["Ölçüt", "Değer"], [
        ["Ortanca başlık uzunluğu", f"{a['median_len']:.0f} karakter"],
        ["Sayı içeren başlık", f"%{a['pct_number']:.0f}"],
        ["Soru işareti içeren", f"%{a['pct_question']:.0f}"],
        ["BÜYÜK HARFLİ kelime içeren", f"%{a['pct_caps']:.0f}"],
        ["Parantez içeren", f"%{a['pct_bracket']:.0f}"],
        ["Ortanca video süresi", f"{a['median_minutes']:.1f} dk"],
    ]))
    out += ["", "## En sık geçen başlık kelimeleri", "",
            ", ".join(f"{w} ({c})" for w, c in a["top_words"]) or "-",
            "", "## En sık kullanılan etiketler", "",
            ", ".join(f"{t} ({c})" for t, c in a["top_tags"]) or "-",
            "", "## En çok izlenen videolar", "",
            yt.md_table(["İzlenme", "Günlük", "Kanal", "Başlık"],
                        [[yt.fmt(v["views"]), yt.fmt(yt.views_per_day(v)), v["channel"], v["title"]] for v in top[:15]])]
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("sorgu")
    p.add_argument("--adet", type=int, default=25, help="incelenecek video sayısı (en fazla 50)")
    p.add_argument("--bolge", default="TR")
    p.add_argument("--dil", default="tr")
    p.add_argument("--cikti")
    args = p.parse_args()
    data = yt.api_get("search", part="id", q=args.sorgu, type="video", order="viewCount",
                      maxResults=min(args.adet, 50), regionCode=args.bolge, relevanceLanguage=args.dil)
    ids = [it["id"]["videoId"] for it in data.get("items", [])]
    yt.emit(report(args.sorgu, yt.video_details(ids)), args.cikti)


if __name__ == "__main__":
    yt.run(main)
