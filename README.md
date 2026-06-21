<div align="center">

# ✂️ Mecha Snippet

### Expansor de texto nativo para macOS. Escribe `//`, busca y pega.

Un panel flotante con fondo Liquid Glass que aparece en cualquier app cuando escribes `//`.
Local, liviano y sin nube.

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![macOS](https://img.shields.io/badge/macOS-Apple%20Silicon-111111?logo=apple&logoColor=white)](https://www.apple.com/macos/)
[![PyObjC](https://img.shields.io/badge/UI-PyObjC%20nativo-4B8BBE)](https://pyobjc.readthedocs.io/)
[![License](https://img.shields.io/badge/License-MIT-22aa55)](LICENSE)
[![Por MechatronicStore](https://img.shields.io/badge/por-MechatronicStore-FF6A00)](https://mechatronicstore.cl)

[![Descargar DMG](https://img.shields.io/github/v/release/PabloSilvaBravo/mecha-snippet?label=Descargar%20DMG&color=0a7a3a)](https://github.com/PabloSilvaBravo/mecha-snippet/releases/latest)

</div>

---

## ⬇️ Descargar (macOS Apple Silicon)

1. Baja el **[DMG más reciente](https://github.com/PabloSilvaBravo/mecha-snippet/releases/latest)**.
2. Ábrelo y arrastra **Mecha Snippet** a la carpeta **Aplicaciones**.
3. La primera vez: **clic derecho sobre la app → Abrir** (no está notarizada por Apple, así que macOS pide confirmar una sola vez).
4. Concede **Accesibilidad** y **Monitoreo de entrada** en Ajustes del Sistema > Privacidad y seguridad, y reábrela.
5. Listo: escribe `//` en cualquier app.

> ¿Prefieres correrla desde el código? Mira la sección **Instalación (desarrollo)** más abajo.

## ✨ Qué hace

- ⚡ **Disparador global `//`** en cualquier aplicación, sin abrir nada.
- 🪟 **Panel Liquid Glass** centrado en pantalla y arrastrable.
- 🔎 **Buscador en tiempo real** (sin tildes, multipalabra, con ranking) y navegación con `↑` `↓`.
- 👁️ **Vista previa del texto completo** del snippet al hacer clic o navegar con flechas.
- 📋 **Enter** borra el `//` y pega el snippet completo, incluso multilínea.
- 🍫 **Ícono en la barra de menú**: recargar, abrir el archivo, pausar, salir.
- 🚀 **Escala a miles de snippets** (carga en memoria + lista virtualizada).
- 🔒 **100% local**: sin servicios externos, sin telemetría, sin nube.

## ⚙️ Cómo funciona

```
mechasnippet/
├── app.py        Ciclo de vida, ícono de barra de menú, cableado general
├── hotkey.py     Listener de teclado global (pynput) que detecta "//"
├── panel.py      Panel Liquid Glass: buscador, lista y vista previa (centrado/arrastrable)
├── inserter.py   Borra "//" y pega el snippet (NSPasteboard + Cmd+V)
├── store.py      Carga/recarga de snippets.json en memoria
├── matcher.py    Filtro en tiempo real (sin tildes, multipalabra, con ranking)
└── paths.py      Rutas (Application Support, etc.)
```

**Flujo:** `hotkey` detecta `//` y avisa al hilo principal, `panel` aparece centrado,
escribes para filtrar, `Enter` cierra el panel, reactiva la app anterior, borra el
`//` y pega el snippet vía portapapeles (restaurando tu portapapeles original después).

**Stack:** Python 3 + PyObjC (AppKit/Quartz nativos) + pynput. La app se registra como
*accessory* (`LSUIElement`): no aparece en el Dock y su consumo en reposo es mínimo
(el listener es por eventos, no hace polling).

## 🚀 Instalación (desarrollo)

```bash
cd mecha-snippet
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m mechasnippet
```

La primera vez se crea tu archivo real de snippets en
`~/Library/Application Support/MechaSnippet/snippets.json` (copiado desde
`snippets.example.json`). Edítalo con tus propios snippets.

### Permisos de macOS (imprescindible)

Para detectar el teclado de forma global y pegar texto, el sistema pide permisos.
Ve a **Ajustes del Sistema > Privacidad y seguridad** y habilita la app (o tu
terminal, en desarrollo) en:

1. **Accesibilidad** (necesario para pegar con `Cmd+V`)
2. **Monitoreo de entrada** (necesario para escuchar el `//`)

Tras concederlos, reinicia la app (el permiso se toma al arrancar).

## ⌨️ Uso

1. Escribe `//` en cualquier app (Notas, Mail, navegador, etc.).
2. Aparece el panel centrado. Escribe para filtrar; navega con `↑` `↓`.
3. Haz clic en un snippet o navega con flechas para ver su texto completo en la vista previa.
4. `Enter` pega el snippet seleccionado (o doble clic en la lista).
5. `Esc` o clic fuera para cerrar. Puedes arrastrar el panel para moverlo.

El disparador no se activa dentro de URLs (no salta con `http://`).

## 📝 Formato de snippets.json

Objeto simple `nombre: contenido` (los saltos de línea van como `\n`):

```json
{
  "pago": "Los datos de transferencia son:\n\nEMPRESA SPA\n00.000.000-0\nCta. Corriente ...",
  "saludo": "Hola, gracias por escribir."
}
```

También se acepta una lista de objetos `{"name": "...", "content": "..."}`.
Tras editar el archivo, usa **Recargar snippets** en el menú (o reinicia).

### Cambiar dónde se guarda (opcional)

Define `MECHA_SNIPPET_FILE` para usar otra ruta (archivo o carpeta):

```bash
export MECHA_SNIPPET_FILE="$HOME/Documentos/mis-snippets.json"
python -m mechasnippet
```

## 📦 Empaquetar como .app

```bash
source .venv/bin/activate
pip install -r requirements-build.txt
python setup.py py2app
open dist/
```

Arrastra `Mecha Snippet.app` a `/Applications` y vuelve a concederle Accesibilidad y
Monitoreo de entrada. Para un arranque estable conviene firmarla con tu Developer ID.

## 🔒 Seguridad y privacidad

**El código es público; tu contenido es privado y local en cada Mac.**

- Tus snippets viven **solo en tu equipo**: `~/Library/Application Support/MechaSnippet/snippets.json`.
- **Sin red, sin telemetría, sin nube.** Cargar, buscar y pegar ocurre 100% en memoria local.
- El `snippets.json` real está en `.gitignore`: **nunca se sube**. El repo solo trae
  `snippets.example.json` con datos ficticios.
- El archivo no está cifrado (JSON en claro). Queda protegido por tu cuenta de macOS y
  FileVault. Si lo respaldas o sincronizas, hazlo por un canal privado tuyo, nunca público.

## 🩺 Solución de problemas

- **No pasa nada al escribir `//`:** revisa Accesibilidad y Monitoreo de entrada, y
  reinicia la app (el permiso se toma al arrancar).
- **No pega el texto:** confirma el permiso de **Accesibilidad** (necesario para `Cmd+V`);
  es distinto del de Monitoreo de entrada.

## 📄 Licencia

MIT. Ver [`LICENSE`](LICENSE).

---

<div align="center">

Hecho por **[MechatronicStore](https://mechatronicstore.cl)**, electrónica y mundo maker en Chile.

</div>
