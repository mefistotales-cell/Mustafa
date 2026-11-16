---
name: referans-analiz
description: 'Bir referans videonun (rakip ya da örnek alınan video) yapısını çıkarır: kesme noktaları ve plan süreleri (pyscenedetect), tempo ve vuruşlar (librosa), konuşma metni (whisper), istenirse sesi müzikten ayırma (demucs); bağlantı verilirse önce yt-dlp ile indirir. Kullanıcı "bu videoyu analiz et", "bu video neden tuttu", "bunun gibi bir video yapalım", "kurgusunu/ritmini çıkar" dediğinde ya da bir video bağlantısını örnek gösterdiğinde kullan. Kesme, birleştirme ve dışa aktarma için ffmpeg-skill; uzun videodan otomatik Shorts için peakcut.'
---

# Referans video analizi

Örnek alınan bir videonun "iskeletini" çıkarıp kendi videonuzu ona göre planlamak için. Araçlar depo kökündeki
`.referans/` klasörüne kurulur (git yok sayar).

## Nasıl

1. Kur (her yeni oturumda bir kez): `bash .claude/skills/referans-analiz/kur.sh`
   Ek seçenekler: `--demucs` (yaklaşık 5 GB indirir), `--blender` (apt ile Blender).
2. Analiz et:
   `.referans/venv/bin/python .claude/skills/referans-analiz/analiz.py VIDEO_YA_DA_BAĞLANTI --cikti raporlar/ref --dil tr`
   Seçenekler: `--model tiny|base|small|medium|large-v3`, `--metinsiz`, `--ses-ayir`.
3. Çıktı: `<ad>_analiz.md` ve `<ad>_analiz.json`. Rapor; süre, plan sayısı, ortalama/ortanca plan süresi, ilk 30
   saniyedeki plan sayısı, tempo, vuruşa denk gelen kesme oranı, konuşma hızı, kanca metni, plan tablosu ve tam
   metni içerir. `raporlar/` git tarafından yok sayılır.
4. Raporu depodaki promptlarla birleştir: kanca ve akış için `prompts/05-senaryo-ve-kanca.md`, otopsi için
   `prompts/08-analiz-ve-iyilestirme.md`. Kullanıcıya ham tabloyu değil, çıkarılacak dersleri anlat.

## Tweet'teki zincirin geri kalanı

| Araç | Durum |
|---|---|
| yt-dlp, pyscenedetect, librosa, whisper, demucs | `analiz.py` içinde |
| ffmpeg | `ffmpeg-skill` becerisi |
| blender | `kur.sh --blender`; sahneyi Python betiğiyle kur, `blender -b -P betik.py` ile arayüzsüz render al |
| puppeteer | Bulut ortamında Playwright ve Chromium hazır kurulu; HTML/CSS animasyonunu kare kare ekran görüntüsü alıp ffmpeg ile birleştir. Kendi bilgisayarında `npm i puppeteer` |
| google flow | Web hizmeti, Google hesabı ister; kurulamaz. Kullanıcı görselleri orada üretip dosya olarak verir |
| voicestudio (ses klonlama) | Kurulu değil; hangi ürün olduğu belirsiz. Ses klonlama yalnızca kullanıcının kendi sesiyle ya da ses sahibinin açık izniyle yapılır |

## Bilinmesi gerekenler

- `analiz.py` yazıldı ama henüz gerçek bir videoyla çalıştırılmadı; ilk kullanımda çıkan hatayı düzelt ve bu satırı sil.
- Whisper modeli ilk kullanımda indirilir (`small` yaklaşık 500 MB). Ağ engellerse `--metinsiz` ile devam et ve söyle.
- Bulut ortamında YouTube indirmeleri engellenebilir (ağ kuralı ya da bot denetimi). Olmazsa kullanıcıdan dosyayı
  yüklemesini iste.
- Referans video yalnızca incelemek içindir: başkasının görüntüsünü, müziğini ya da metnini yeni videoda kullanma;
  yapıyı ve tekniği örnek al.
- Bu ortamda `download.pytorch.org` engelli olduğundan demucs, PyPI'deki büyük torch paketiyle kurulur.
