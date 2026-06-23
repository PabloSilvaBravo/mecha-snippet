<div align="center">

# ✂️ Mecha Snippet

### Expansor de texto nativo para macOS. Escribe `//`, busca y pega.

Un panel flotante con Liquid Glass que aparece en cualquier app cuando escribes `//`.
Local, liviano y sin nube. Ahora reescrito en Swift nativo.

[![Swift](https://img.shields.io/badge/Swift-6-F05138?logo=swift&logoColor=white)](https://swift.org/)
[![macOS](https://img.shields.io/badge/macOS-26%20Tahoe-111111?logo=apple&logoColor=white)](https://www.apple.com/macos/)
[![Liquid Glass](https://img.shields.io/badge/UI-SwiftUI%20%2B%20AppKit-4B8BBE)](https://developer.apple.com/xcode/swiftui/)
[![License](https://img.shields.io/badge/License-MIT-22aa55)](LICENSE)
[![por Pablo Silva Bravo](https://img.shields.io/badge/por-Pablo%20Silva%20Bravo-4B8BBE)](https://github.com/PabloSilvaBravo)

[![Descargar DMG](https://img.shields.io/github/v/release/PabloSilvaBravo/mecha-snippet?label=Descargar%20DMG&color=0a7a3a)](https://github.com/PabloSilvaBravo/mecha-snippet/releases/latest)

</div>

---

## ⬇️ Descargar (macOS 26 Tahoe, Apple Silicon)

1. Baja el **[DMG más reciente](https://github.com/PabloSilvaBravo/mecha-snippet/releases/latest)**.
2. Ábrelo y arrastra **Mecha Snippet** a la carpeta **Aplicaciones**.
3. La primera vez: clic derecho sobre la app y luego **Abrir** (no está notarizada por Apple, así que macOS pide confirmar una sola vez).
4. Al abrirla por primera vez te guía para conceder los dos permisos que necesita.
5. Listo: escribe `//` en cualquier app.

> ¿Prefieres correrla desde el código? Mira **Desarrollo** más abajo.

## ✨ Qué hace

- ⚡ **Disparador global `//`** en cualquier aplicación, sin abrir nada.
- 🪟 **Panel Liquid Glass** con la lista a la izquierda y la **vista previa a la derecha**. Recuerda dónde lo dejaste.
- 🔎 **Buscador en tiempo real** (sin tildes, multipalabra, con ranking) y navegación con `↑` `↓`.
- 📋 **Enter** borra el `//` y pega el snippet completo, preservando tu portapapeles.
- ✏️ **Editor visual de snippets**: una ventana de gestión para crear, editar, borrar, duplicar y **reordenar arrastrando**, más un mini formulario para sumar uno rápido. Sin tocar JSON a mano.
- 🚀 **Inicio automático**: arranca al abrir sesión y se mantiene activo.
- 🧭 **Onboarding** que te guía a conceder los permisos en la primera corrida.
- 🍫 **Ícono en la barra de menú**: buscar, nuevo, gestionar, recargar, pausar, salir.
- 🔒 **100% local**: sin servicios externos, sin telemetría, sin nube.

## ⚙️ Cómo funciona

- **Núcleo** (`MechaSnippetCore`): modelo, almacenamiento y búsqueda. Lógica pura con tests.
- **App** (`MechaSnippet`): SwiftUI para las vistas (gestión, mini formulario, onboarding, menú) y AppKit para el panel flotante no activante y el `CGEventTap` global.

**Flujo:** el `CGEventTap` detecta `//`, aparece el panel, escribes para filtrar, `Enter` lo cierra, reactiva la app anterior, borra el `//` y pega el snippet vía portapapeles (restaurando el tuyo después). La app es de barra de menú (`LSUIElement`): sin ícono en el Dock y con consumo mínimo en reposo.

## 🚀 Desarrollo

Requiere Xcode 26 (o Command Line Tools con Swift 6.2+) en Apple Silicon.

```bash
git clone https://github.com/PabloSilvaBravo/mecha-snippet.git
cd mecha-snippet
swift build              # compilar
swift test              # tests del núcleo
./Scripts/build_app.sh  # empaquetar y firmar dist/Mecha Snippet.app
```

Para el ícono y el DMG:

```bash
swift Scripts/make_icon_source.swift && ./Scripts/make_icon.sh
./Scripts/make_dmg.sh   # genera dist/MechaSnippet-<version>.dmg
```

### Permisos de macOS

La app pide dos permisos en **Ajustes del Sistema > Privacidad y seguridad**:

1. **Monitoreo de entrada**: para escuchar el `//`.
2. **Accesibilidad**: para pegar con `Cmd+V`.

El onboarding de la app te lleva al panel exacto de cada uno y detecta cuando los concedes.

## 📝 Formato de snippets.json

Tus snippets viven en `~/Library/Application Support/MechaSnippet/snippets.json`.
El formato es una lista de objetos `{name, content}` (los saltos de línea van como `\n`):

```json
[
  { "name": "saludo", "content": "Hola, ¿en qué te puedo ayudar?" },
  { "name": "pago", "content": "Datos de transferencia:\n\nEMPRESA SPA\n..." }
]
```

También se acepta el formato antiguo `{ "nombre": "contenido" }`, y la app repara
solo los archivos que quedaron con comillas tipográficas (por ejemplo, al editarlos
en TextEdit). Lo más cómodo igual es usar el editor visual de la app.

## 🔒 Seguridad y privacidad

**El código es público; tu contenido es privado y local en cada Mac.**

- Tus snippets viven solo en tu equipo, en `Application Support`.
- Sin red, sin telemetría, sin nube. Cargar, buscar y pegar ocurre 100% en memoria local.
- El `snippets.json` real está en `.gitignore`: nunca se sube. El repo solo trae
  `snippets.example.json` con datos ficticios.
- El archivo no está cifrado. Queda protegido por tu cuenta de macOS y FileVault.

## 📄 Licencia

MIT. Ver [`LICENSE`](LICENSE).

---

<div align="center">

Hecho por **[Pablo Silva Bravo](https://github.com/PabloSilvaBravo)**.

</div>
