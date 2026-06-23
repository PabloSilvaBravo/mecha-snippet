#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION="${1:-2.0.0}"
APP_DST="/Applications/Mecha Snippet.app"

./Scripts/build_app.sh "$VERSION"

echo "==> cerrando instancias en ejecución"
pkill -f "Mecha Snippet" 2>/dev/null || true
sleep 1

echo "==> instalando en /Applications (una sola copia)"
rm -rf "$APP_DST"
cp -R "dist/Mecha Snippet.app" "$APP_DST"

# Clave: NO dejar una segunda copia con el mismo bundle id. Dos apps con el
# mismo identifier impiden que macOS registre los permisos (Input Monitoring /
# Accesibilidad). Por eso borramos la copia de build.
rm -rf "dist/Mecha Snippet.app"

echo "==> instalado: $APP_DST (sin copia duplicada en dist/)"