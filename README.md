# YouTube Kanal Geliştirme Promptları

YouTube kanalının izlenmesini artırmak için hazır promptlar. Her prompt bir yapay zekâ asistanına (Claude vb.) kopyalanıp yapıştırılacak şekilde yazıldı.

## Nasıl kullanılır

1. Aşağıdaki **Kanal Kimliği** bloğunu bir kez doldurun.
2. Kullanacağınız promptun başına bu bloğu yapıştırın.
3. Prompt içindeki `[KÖŞELİ PARANTEZ]` alanlarını kendi bilginizle değiştirin.

```text
KANAL KİMLİĞİ
- Kanal adı: [KANAL ADI]
- Niş / konu: [NİŞ]
- Hedef izleyici: [YAŞ, İLGİ ALANI, SORUNLARI]
- Video dili ve üslup: [ÖR. TÜRKÇE, SAMİMİ, HIZLI]
- Video türü: [UZUN VİDEO / SHORTS / İKİSİ]
- Abone sayısı ve ortalama izlenme: [SAYILAR]
- En iyi 3 videom: [BAŞLIKLAR VE İZLENMELERİ]
- Rakip / örnek kanallar: [KANALLAR]
```

## İçindekiler

| Dosya | Ne işe yarar |
|---|---|
| [01 Kanal stratejisi](prompts/01-kanal-stratejisi.md) | Niş, konumlandırma, içerik sütunları, 90 günlük plan |
| [02 Video fikirleri](prompts/02-video-fikirleri.md) | Talep gören konu bulma, seri ve trend fikirleri |
| [03 Başlıklar](prompts/03-basliklar.md) | Tıklanma oranını artıran başlık üretimi ve testi |
| [04 Küçük resimler](prompts/04-kucuk-resimler.md) | Thumbnail konsepti, metni ve görsel üretim promptu |
| [05 Senaryo ve kanca](prompts/05-senaryo-ve-kanca.md) | İlk 30 saniye, senaryo yapısı, izleyici tutma |
| [06 SEO](prompts/06-seo-aciklama-etiket.md) | Anahtar kelime, açıklama, etiket, bölümler |
| [07 Shorts](prompts/07-shorts.md) | Kısa video fikirleri, kancaları, uzun videodan kesme |
| [08 Analiz](prompts/08-analiz-ve-iyilestirme.md) | YouTube Studio verisini yorumlama, video otopsisi |
| [09 Topluluk](prompts/09-topluluk-ve-etkilesim.md) | Yorum, topluluk gönderisi, abone çağrısı |
| [10 Tanıtım](prompts/10-yeniden-kullanim-ve-tanitim.md) | Diğer platformlarda dağıtım, iş birliği |

## Analiz araçları

`tools/` klasöründe YouTube Data API ile çalışan üç komut satırı aracı var. Yalnızca Python 3.9+ gerekir; ek paket kurulmaz. Çıktılar Markdown rapordur ve promptlara doğrudan yapıştırılabilir.

| Komut | Ne yapar |
|---|---|
| `python3 -m tools.baslik_analizi "arama ifadesi"` | Bir aramada en çok izlenen videoların başlık, etiket ve süre kalıplarını çıkarır (çalıştırma başına 100 kota birimi) |
| `python3 -m tools.rakip_takibi @kanal1 @kanal2` | Rakip kanalların, kendi ortancasının en az 2 katı izlenen videolarını bulur |
| `python3 -m tools.yayin_zamani @kanalim` | Videolarınızı yayın günü ve saatine göre karşılaştırır |

Ortak seçenekler: `--cikti rapor.md` (dosyaya yaz), `--shorts-haric` (60 saniye ve altını sayma), `--adet N`. Tümü için `--help`.

**API anahtarı:** Google Cloud Console'da "YouTube Data API v3" için bir API anahtarı oluşturun.

- Kendi bilgisayarınızda: `export YOUTUBE_API_KEY=...`
- Claude bulut ortamında: ortam ayarlarında ağ gizli anahtarı olarak `youtube.googleapis.com` adresi ve `X-Goog-Api-Key` başlığıyla kaydedin; değişken gerekmez.

Testler: `python3 -m unittest discover -s tests`

## Video düzenleme (ffmpeg-skill)

`.claude/skills/ffmpeg-skill/` altında [kajisho5/ffmpeg-skill](https://github.com/kajisho5/ffmpeg-skill) (v3.10.1, MIT) kurulu. Bu depoda Claude Code ile çalışırken bir video dosyasından söz etmeniz yeterli; Claude kesme, sessizlik silme, 9:16'ya çevirme, altyazı, ses seviyesi ve platform (YouTube / Shorts) dışa aktarma işlerini yerel FFmpeg ile yapar ve çıktıyı kontrol eder. Bulut ya da API anahtarı gerekmez.

- Gereken: `ffmpeg` 6.1+ ve Python 3.10+. Kontrol: `python3 .claude/skills/ffmpeg-skill/scripts/_contract.py doctor`
- Örnek istek: "`video.mp4` içinden 0:45–3:10 arasını al, sessizlikleri sil, Shorts için 9:16 yap."
- Konuşmadan otomatik altyazı için ayrıca `pip install faster-whisper` gerekir.
- Güncelleme: depo kökünde `npx ffmpeg-skill --project`

## Önerilen iş akışı (her video için)

1. **Fikir:** 02'den konu seçin.
2. **Paket:** 03 ve 04 ile başlık + küçük resmi senaryodan *önce* belirleyin.
3. **Senaryo:** 05 ile kancayı ve akışı yazın.
4. **Yayın:** 06 ile açıklama, etiket ve bölümleri hazırlayın.
5. **Dağıtım:** 07 ve 10 ile Shorts ve diğer platform içeriklerini çıkarın.
6. **Öğrenme:** 48 saat ve 7 gün sonra 08 ile veriyi yorumlayın.

## Not

Bu promptlar gerçek izleyici kazanmaya yöneliktir. Sahte izlenme, bot, abone satın alma veya yanıltıcı başlık (clickbait olup sözünü tutmayan) YouTube kurallarına aykırıdır ve kanalı riske atar.
