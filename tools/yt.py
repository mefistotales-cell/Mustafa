"""YouTube Data API v3 için küçük istemci ve ortak yardımcılar (yalnızca standart kütüphane)."""
import json
import os
import re
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://youtube.googleapis.com/youtube/v3/"


class ApiError(RuntimeError):
    pass


def api_get(resource, **params):
    """Tek bir API çağrısı yapar ve JSON yanıtı döndürür.

    Anahtar YOUTUBE_API_KEY değişkeninden okunur. Bulut ortamında anahtar ağ
    vekili tarafından eklendiği için değişken boşsa yer tutucu gönderilir.
    """
    url = API + resource + "?" + urllib.parse.urlencode(params)
    key = os.environ.get("YOUTUBE_API_KEY") or "ortam-tarafindan-eklenir"
    req = urllib.request.Request(url, headers={"X-Goog-Api-Key": key, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            message = json.loads(body)["error"]["message"]
        except Exception:
            message = body[:300]
        raise ApiError(f"YouTube API hatası {e.code}: {message}") from None
    except urllib.error.URLError as e:
        raise ApiError(f"Ağ hatası: {e.reason}") from None


def resolve_channel(ref):
    """@kullanıcıadı, kanal URL'si veya UC... kimliğinden kanal kaydını döndürür."""
    ref = ref.strip().rstrip("/")
    m = re.search(r"(UC[\w-]{22})", ref)
    params = {"part": "snippet,contentDetails,statistics"}
    if m:
        params["id"] = m.group(1)
    else:
        handle = ref.split("/")[-1]
        params["forHandle"] = handle if handle.startswith("@") else "@" + handle
    items = api_get("channels", **params).get("items", [])
    if not items:
        raise ApiError(f"Kanal bulunamadı: {ref}")
    return items[0]


def video_details(ids):
    """Video kimlikleri için sadeleştirilmiş kayıt listesi döndürür (50'lik gruplar)."""
    out = []
    for i in range(0, len(ids), 50):
        data = api_get("videos", part="snippet,statistics,contentDetails", id=",".join(ids[i:i + 50]), maxResults=50)
        out.extend(simplify(v) for v in data.get("items", []))
    return out


def channel_videos(channel, limit=50):
    """Kanalın en son yüklediği `limit` videoyu döndürür."""
    playlist = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, token = [], None
    while len(ids) < limit:
        params = {"part": "contentDetails", "playlistId": playlist, "maxResults": min(50, limit - len(ids))}
        if token:
            params["pageToken"] = token
        data = api_get("playlistItems", **params)
        ids.extend(it["contentDetails"]["videoId"] for it in data.get("items", []))
        token = data.get("nextPageToken")
        if not token:
            break
    return video_details(ids)


def parse_duration(iso):
    """ISO 8601 süresini (PT1H2M3S) saniyeye çevirir."""
    m = re.fullmatch(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def simplify(v):
    sn, st = v["snippet"], v.get("statistics", {})
    return {
        "id": v["id"],
        "title": sn["title"],
        "channel": sn.get("channelTitle", ""),
        "published": datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00")),
        "tags": sn.get("tags", []),
        "views": int(st.get("viewCount", 0)),
        "likes": int(st.get("likeCount", 0)),
        "comments": int(st.get("commentCount", 0)),
        "seconds": parse_duration(v.get("contentDetails", {}).get("duration")),
    }


def views_per_day(video, now=None):
    now = now or datetime.now(timezone.utc)
    days = max((now - video["published"]).total_seconds() / 86400, 1)
    return video["views"] / days


def median(values):
    values = list(values)
    return statistics.median(values) if values else 0


def fmt(n):
    """Sayıyı Türkçe binlik ayırıcıyla yazar."""
    return f"{round(n):,}".replace(",", ".")


def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(c).replace("|", "/") for c in r) + " |")
    return "\n".join(lines)


def emit(text, path=None):
    if path:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"Rapor yazıldı: {path}", file=sys.stderr)
    else:
        print(text)


def run(main):
    """Komut satırı girişini çalıştırır; API hatalarını okunur biçimde bildirir."""
    try:
        main()
    except ApiError as e:
        sys.exit(f"Hata: {e}")
