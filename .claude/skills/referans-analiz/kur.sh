#!/usr/bin/env bash
# Referans video analiz araçlarını depo kökündeki .referans/ klasörüne kurar (git yok sayar).
#   bash kur.sh             temel: yt-dlp, pyscenedetect, librosa, whisper (faster-whisper)
#   bash kur.sh --demucs    ek olarak demucs (sesi müzikten ayırır; büyük indirme)
#   bash kur.sh --blender   ek olarak Blender (apt ile; büyük indirme, yönetici yetkisi ister)
# Tekrar çalıştırmak güvenlidir.
set -euo pipefail
KOK="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
HEDEF="$KOK/.referans"
mkdir -p "$HEDEF"
[ -x "$HEDEF/venv/bin/python" ] || python3 -m venv "$HEDEF/venv"
PIP=("$HEDEF/venv/bin/pip" install --quiet --disable-pip-version-check)
"${PIP[@]}" yt-dlp scenedetect opencv-python-headless librosa soundfile faster-whisper
for secenek in "$@"; do
  case "$secenek" in
    --demucs)
      # önce küçük olan işlemci sürümünü dene; olmazsa PyPI'deki varsayılanı kur
      "${PIP[@]}" torch torchaudio --index-url https://download.pytorch.org/whl/cpu || true
      "${PIP[@]}" demucs ;;
    --blender)
      command -v blender >/dev/null || { apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq blender; } ;;
    *) echo "Bilinmeyen seçenek: $secenek" >&2; exit 2 ;;
  esac
done
command -v ffmpeg >/dev/null || { echo "ffmpeg bulunamadı: önce ffmpeg kurun." >&2; exit 1; }
echo "Hazır: $HEDEF"
