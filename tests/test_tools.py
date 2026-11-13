import unittest
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from tools import baslik_analizi, rakip_takibi, yayin_zamani, yt

NOW = datetime.now(timezone.utc)


def video(title="Başlık", views=100, days_ago=10, seconds=600, tags=(), published=None):
    return {"id": "x", "title": title, "channel": "Kanal", "tags": list(tags), "views": views,
            "likes": 0, "comments": 0, "seconds": seconds,
            "published": published or NOW - timedelta(days=days_ago)}


class YtTest(unittest.TestCase):
    def test_parse_duration(self):
        self.assertEqual(yt.parse_duration("PT1H2M3S"), 3723)
        self.assertEqual(yt.parse_duration("PT45S"), 45)
        self.assertEqual(yt.parse_duration("P1DT1M"), 86460)
        self.assertEqual(yt.parse_duration(None), 0)

    def test_simplify(self):
        v = yt.simplify({"id": "abc", "snippet": {"title": "T", "publishedAt": "2026-01-02T03:04:05Z"},
                         "statistics": {"viewCount": "42"}, "contentDetails": {"duration": "PT2M"}})
        self.assertEqual((v["views"], v["seconds"], v["likes"], v["tags"]), (42, 120, 0, []))
        self.assertEqual(v["published"].tzinfo, timezone.utc)

    def test_fmt_and_table(self):
        self.assertEqual(yt.fmt(1234567), "1.234.567")
        self.assertIn("| a/b |", yt.md_table(["X"], [["a|b"]]))


class AnalysisTest(unittest.TestCase):
    def test_title_analysis(self):
        a = baslik_analizi.analyze([
            video("YouTube'da 5 HATA yapma", tags=["youtube", "Hata"]),
            video("YouTube nasıl büyür?", tags=["youtube"]),
        ])
        self.assertEqual(a["pct_number"], 50)
        self.assertEqual(a["pct_question"], 50)
        self.assertEqual(a["pct_caps"], 50)
        self.assertEqual(a["top_words"][0], ("youtube", 2))
        self.assertEqual(a["top_tags"][0], ("youtube", 2))

    def test_outliers(self):
        vids = [video(f"v{i}", views=1000) for i in range(5)] + [video("hit", views=10000)]
        hits = rakip_takibi.outliers(vids, 2.0)
        self.assertEqual([v["title"] for v, _ in hits], ["hit"])
        self.assertAlmostEqual(hits[0][1], 10, places=1)
        self.assertEqual(rakip_takibi.outliers([], 2.0), [])

    def test_publish_time_groups_in_local_time(self):
        # 2026-01-04 Pazar 22:30 UTC = Pazartesi 01:30 İstanbul
        v = video(views=500, published=datetime(2026, 1, 4, 22, 30, tzinfo=timezone.utc))
        days, slots = yayin_zamani.group([v], ZoneInfo("Europe/Istanbul"))
        self.assertEqual(days, [("Pazartesi", 1, 500)])
        self.assertEqual(slots, [("00-06", 1, 500)])

    def test_reports_render(self):
        vids = [video("Deneme 1", views=10), video("Deneme 2", views=90)]
        self.assertIn("Deneme 2", baslik_analizi.report("q", vids))
        self.assertIn("veri yetersiz", yayin_zamani.report("K", vids, "Europe/Istanbul"))
        ch = {"snippet": {"title": "K"}, "statistics": {}}
        self.assertIn("gizli", rakip_takibi.report([(ch, vids)], 2.0))


if __name__ == "__main__":
    unittest.main()
