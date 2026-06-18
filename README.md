# Mecha Snippet

Expansor de texto nativo para **macOS (Apple Silicon)**, escrito en Python.

Corre en segundo plano y, cuando escribes `//` en cualquier app, abre un panel
flotante junto al cursor para buscar tus snippets y pegarlos al instante.

- Detección global del disparador `//` en cualquier aplicación.
- Panel flotante con buscador en tiempo real y navegación con `↑` `↓`.
- `Enter` borra el `//` y pega el snippet completo (soporta texto multilínea).
- `Esc` o click fuera para cerrar.
- Ícono en la barra de menú: recargar, abrir el archivo, pausar, salir.
- Escala a miles de snippets (carga en memoria + lista virtualizada).
- 100% local: sin servicios externos ni nube.

## Cómo funciona (arquitectura)

```
mechasnippet/
├── app.py        Ciclo de vida, ícono de barra de menú, cableado general
├── hotkey.py     Listener de teclado global (pynput) que detecta "//"
├── panel.py      NSPanel flotante: buscador + lista de resultados
├── caret.py      Posición del panel (cursor de texto vía Accesibilidad, o mouse)
├── inserter.py   Borra "//" y pega el snippet (NSPasteboard + Cmd+V)
├── store.py      Carga/recarga de snippets.json en memoria
├── matcher.py    Filtro en tiempo real (sin tildes, multipalabra, con ranking)
└── paths.py      Rutas (Application Support, etc.)
```

**Flujo:** `hotkey` detecta `//` y avisa al hilo principal, `panel` aparece junto
al cursor, escribes para filtrar, `Enter` cierra el panel, reactiva la app
anterior, borra el `//` y pega el snippet vía portapapeles (restaurando tu
portapapeles original después).

**Stack:** Python 3 + PyObjC (AppKit/Quartz nativos) + pynput. La app se registra
como *accessory* (`LSUIElement`), así que no aparece en el Dock y su consumo en
reposo es mínimo (el listener es por eventos, no hace polling).

## Requisitos

- macOS 12 o superior (Apple Silicon).
- Python 3.9+ (recomendado el del sistema o uno de Homebrew: `brew install python`).

## Instalación (desarrollo)

```bash
cd mecha-snippet
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m mechasnippet
```

La primera vez se crea tu archivo real de snippets en:

```
~/Library/Application Support/MechaSnippet/snippets.json
```

(se copia desde `snippets.example.json`). Edítalo con tus propios snippets.

### Permisos de macOS (imprescindible)

Para detectar el teclado de forma global y pegar texto, el sistema pide permisos.
Ve a **Ajustes del Sistema > Privacidad y seguridad** y agrega tu terminal (en
desarrollo) o `Mecha Snippet.app` (empaquetada) en:

1. **Accesibilidad**
2. **Monitoreo de entrada**

Sin estos permisos el disparador `//` no se detecta. Tras concederlos, reinicia
la app.

## Uso

1. Escribe `//` en cualquier app (Notas, Mail, navegador, etc.).
2. Aparece el panel. Escribe para filtrar; navega con `↑` `↓`.
3. `Enter` pega el snippet seleccionado (o doble click en la lista).
4. `Esc` o click fuera para cerrar sin pegar.

El disparador NO se activa dentro de URLs (`http://`) ni de `///`.

## Formato de snippets.json

Objeto simple `nombre: contenido` (los saltos de línea van como `\n`):

```json
{
  "pago": "Los datos de transferencia son:\n\nEMPRESA SPA\n00.000.000-0\nCta. Corriente ...",
  "saludo": "Hola, gracias por escribir."
}
```

También se acepta una lista de objetos `{"name": "...", "content": "..."}`.
Tras editar el archivo, usa **Recargar snippets** en el menú (o reinicia).

## Empaquetar como .app

```bash
source .venv/bin/activate
pip install -r requirements-build.txt
python setup.py py2app
open dist/
```

Arrastra `Mecha Snippet.app` a `/Applications`. La primera vez vuelve a
concederle Accesibilidad y Monitoreo de entrada (ahora a la app, no a la terminal).

> Nota sobre firma: si reconstruyes la app, macOS puede pedir los permisos de
> nuevo (cambia la firma). Para uso personal con build ad-hoc es normal. Para una
> instalación estable conviene firmarla con tu Developer ID.

### Arranque automático al iniciar sesión

**Ajustes del Sistema > General > Ítems de inicio de sesión > +** y agrega
`Mecha Snippet.app`. Al ser `LSUIElement` arranca invisible, solo con su ícono
en la barra de menú.

## Seguridad y privacidad

- Tu `snippets.json` **real vive fuera del repo** (Application Support) y está en
  `.gitignore`. **Nunca se sube a GitHub.**
- El repo público solo incluye `snippets.example.json` con **datos ficticios**.
- No hay red, ni telemetría, ni nube. Todo es local.
- **No pongas tus datos reales en `snippets.example.json`** ni hagas commit de un
  `snippets.json` con información sensible.

## Rendimiento

- Reposo: sin uso de CPU (listener por eventos).
- RAM: del orden de decenas de MB (Python + PyObjC).
- Miles de snippets: carga en memoria una vez y filtro instantáneo; la lista solo
  dibuja las filas visibles.

## Solución de problemas

- **No pasa nada al escribir `//`:** revisa Accesibilidad y Monitoreo de entrada,
  y reinicia la app.
- **Aparece junto al mouse y no al cursor de texto:** esa app no expone la
  posición del caret vía Accesibilidad; es el comportamiento de respaldo.
- **No pega el texto:** confirma el permiso de Accesibilidad (necesario para
  enviar `Cmd+V`).

## Licencia

MIT. Ver `LICENSE`.
