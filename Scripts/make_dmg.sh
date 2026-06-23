#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION="${1:-2.0.0}"
APP="dist/Mecha Snippet.app"
DMG="dist/MechaSnippet-$VERSION.dmg"
[ -d "$APP" ] || { echo "Falta $APP. Corre Scripts/build_app.sh primero."; exit 1; }

STAGING="$(mktemp -d)"
cp -R "$APP" "$STAGING/"
ln -s /Applications "$STAGING/Applications"
rm -f "$DMG"
hdiutil create -volname "Mecha Snippet" -srcfolder "$STAGING" -ov -format UDZO "$DMG" >/dev/null
echo "==> $DMG"
