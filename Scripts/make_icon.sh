#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

SRC="Resources/icon-source.png"
[ -f "$SRC" ] || { echo "Falta $SRC. Corre: swift Scripts/make_icon_source.swift"; exit 1; }

ICONSET="$(mktemp -d)/AppIcon.iconset"
mkdir -p "$ICONSET"
for s in 16 32 128 256 512; do
  sips -z "$s" "$s" "$SRC" --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
  sips -z "$((s*2))" "$((s*2))" "$SRC" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o Scripts/AppIcon.icns
echo "==> Scripts/AppIcon.icns generado"
