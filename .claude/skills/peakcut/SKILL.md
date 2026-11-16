---
name: peakcut
description: 'Uzun bir videodan otomatik olarak paylaşılmaya hazır dikey (9:16) Shorts/Reels/TikTok klipleri çıkarır: konuşmayı yazıya döker, öne çıkan anları seçer, kelime kelime altyazı ve kanca yazısı ekler. Kullanıcı uzun bir video dosyası verip "bundan Shorts çıkar", "en iyi anları kes", "klip üret" dediğinde kullan. Belirli bir aralığı kesmek, tek bir videoyu düzeltmek veya ses/altyazı ayarı gibi elle yapılan işler için bunu değil ffmpeg-skill kullan.'
---

# PeakCut

[PeakCut](https://github.com/haziqahmedqasmi/PeakCut) (MIT) kendi başına çalışan bir web uygulamasıdır. Bu beceri onu
depo kökündeki `.peakcut/` klasörüne kurar (git yok sayar) ve komut satırından sürer.

## Ne zaman

- Uzun video (yaklaşık 1 dakikadan uzun, konuşma içeren) → birkaç dikey klip: **bu beceri**.
- Kullanıcı hangi saniyeleri istediğini söylüyorsa, ya da tek klibi düzeltmek/yeniden biçimlendirmek gerekiyorsa:
  **ffmpeg-skill**. PeakCut'ın ürettiği klibi sonradan ffmpeg-skill ile düzeltmek (ses seviyesi, kırpma, kontrol) olağandır.

## Nasıl

1. Kur (her yeni oturumda bir kez; kuruluysa saniyeler sürer):
   `bash .claude/skills/peakcut/kur.sh`
2. Klip üret:
   `.peakcut/venv/bin/python .claude/skills/peakcut/klip.py VIDEO --cikti klipler/`
   Seçenekler: `--adet N`, `--en-kisa SN`, `--en-uzun SN`, `--stil bounce|hype|clean`.
   Sunucuyu kendisi başlatıp kapatır. İlk çalıştırmada yaklaşık 480 MB konuşma modeli iner; uzun süren işleri
   arka planda çalıştır.
3. Çıktı: `klipler/` altında `<video>_clipNN.mp4` dosyaları ve `<video>_klipler.json` (başlangıç/bitiş, kanca,
   başlık, seçilme nedeni). Kullanıcıya göstermeden önce her klipten bir kare çıkarıp bak ve
   `ffmpeg-skill` içindeki `check.py --platform shorts` ile ölç.

## Bilinmesi gerekenler

- **Yapay zekâ anahtarı yoksa** klipler yalnızca ses yüksekliğine göre seçilir, kanca "WAIT FOR IT" olur, başlık ve
  etiket üretilmez (JSON'da `yapay_zeka.used: false`). Bunu kullanıcıya açıkça söyle. Bu durumda başlık, açıklama ve
  kancayı `prompts/03-basliklar.md` ve `prompts/07-shorts.md` ile kendin yaz. Anahtar için ortam değişkenleri:
  `PEAKCUT_AI_PROVIDER`, `PEAKCUT_AI_MODELS`, `PEAKCUT_AI_KEY` (anahtarı asla depoya yazma).
- **Türkçe konuşma tanıma denenmedi.** Türkçe videoda önce altyazıların doğruluğunu bir iki kareden kontrol et;
  kötüyse bunu söyle ve altyazıyı ffmpeg-skill'in `caption.py` aracıyla ayrıca üretmeyi öner.
- YouTube/Twitch bağlantısından indirme, canlı yayın kırpma ve hesaplara otomatik paylaşım uygulamada var ama bu
  beceriyle sürülmüyor ve denenmedi. Bağlantıdan indirme yalnızca kullanıcının kendi videoları ya da izni olan
  videolar içindir. Paylaşımı kullanıcı açıkça istemeden yapma.
- Tarayıcı arayüzü gerekirse: `cd .peakcut/app && PEAKCUT_DATA=../data ../venv/bin/python -m studio.server`,
  ardından `http://127.0.0.1:8765`.
- Sürüm `kur.sh` içindeki `SURUM` satırıyla sabitlenmiştir.
