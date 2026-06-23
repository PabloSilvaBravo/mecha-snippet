#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION="${1:-2.0.0}"
APP="dist/Mecha Snippet.app"
SIGN_ID="Apple Development: pablo.silva.bravo.alexa@gmail.com (2PBTW45X92)"

echo "==> swift build (release)"
swift build -c release

BIN=".build/release/MechaSnippet"

echo "==> armando $APP"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cp "$BIN" "$APP/Contents/MacOS/MechaSnippet"

# Recursos planos en Contents/Resources/ (sin resource bundles de SwiftPM, que
# rompen la firma para TCC). Se leen con Bundle.main.
cp "Resources/snippets.example.json" "$APP/Contents/Resources/snippets.example.json"

sed "s/__VERSION__/$VERSION/g" Scripts/Info.plist.template > "$APP/Contents/Info.plist"

# Ícono (si existe el .icns ya generado en la tarea 14)
[ -f "Scripts/AppIcon.icns" ] && cp "Scripts/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"

# LaunchAgent embebido para auto-arranque (lo usa la tarea 11)
if [ -f "Scripts/LaunchAgent.plist" ]; then
  mkdir -p "$APP/Contents/Library/LaunchAgents"
  cp "Scripts/LaunchAgent.plist" "$APP/Contents/Library/LaunchAgents/io.github.pablosilvabravo.mechasnippet.plist"
fi

echo "==> firmando"
# Sin --deep y sin resource bundles anidados: firma simple y consistente, que es
# lo que TCC exige para Input Monitoring / Accesibilidad.
codesign --force --options runtime --sign "$SIGN_ID" "$APP"
echo "==> verificando firma (estricta)"
codesign --verify --deep --strict --verbose=2 "$APP"
echo "==> listo: $APP"
