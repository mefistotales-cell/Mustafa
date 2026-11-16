#!/usr/bin/env bash
# PeakCut'ı depo kökündeki .peakcut/ klasörüne kurar (git tarafından yok sayılır).
# Tekrar çalıştırmak güvenlidir: kurulu olanı atlar.
set -euo pipefail
SURUM=b3e403e27444b620a50a4ec1cf44b3afff9e9e45   # denenmiş sürüm; güncellemek için bu satırı değiştirin
KOK="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
HEDEF="$KOK/.peakcut"
mkdir -p "$HEDEF"
if [ ! -d "$HEDEF/app/.git" ]; then
  git clone --quiet https://github.com/haziqahmedqasmi/PeakCut "$HEDEF/app"
fi
if [ "$(git -C "$HEDEF/app" rev-parse HEAD)" != "$SURUM" ]; then
  git -C "$HEDEF/app" fetch --quiet origin "$SURUM" 2>/dev/null || git -C "$HEDEF/app" fetch --quiet origin
  git -C "$HEDEF/app" checkout --quiet "$SURUM"
fi
if [ ! -x "$HEDEF/venv/bin/python" ]; then
  python3 -m venv "$HEDEF/venv"
fi
"$HEDEF/venv/bin/pip" install --quiet --disable-pip-version-check -r "$HEDEF/app/requirements.txt"
command -v ffmpeg >/dev/null || { echo "ffmpeg bulunamadı: önce ffmpeg kurun." >&2; exit 1; }
echo "PeakCut hazır: $HEDEF"
