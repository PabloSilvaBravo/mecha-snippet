# Mecha Snippet

Expansor de texto nativo para **macOS (Apple Silicon)**, escrito en Python.

Corre en segundo plano y, cuando escribes `//` en cualquier app, abre un panel
flotante centrado para buscar tus snippets y pegarlos al instante.

- Detección global del disparador `//` en cualquier aplicación.
- Panel con fondo Liquid Glass, centrado en pantalla y arrastrable.
- Buscador en tiempo real y navegación con `↑` `↓`.
- Vista previa del texto completo del snippet al hacer clic o navegar con flechas.
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
├── panel.py      Panel Liquid Glass: buscador, lista y vista previa (centrado/arrastrable)
├── inserter.py   Borra "//" y pega el snippet (NSPasteboard + Cmd+V)
├── store.py      Carga/recarga de snippets.json en memoria
├── matcher.py    Filtro en tiempo real (sin tildes, multipalabra, con ranking)
└── paths.py      Rutas (Application Support, etc.)
```

**Flujo:** `hotkey` detecta `//` y avisa al hilo principal, `panel` aparece
centrado en pantalla, escribes para filtrar, `Enter` cierra el panel, reactiva la
app anterior, borra el `//` y pega el snippet vía portapapeles (restaurando tu
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
2. Aparece el panel centrado. Escribe para filtrar; navega con `↑` `↓`.
3. Haz clic en un snippet o navega con flechas para ver su texto completo en la vista previa.
4. `Enter` pega el snippet seleccionado (o doble clic en la lista).
5. `Esc` o clic fuera para cerrar sin pegar. Puedes arrastrar el panel para moverlo.

El disparador no se activa dentro de URLs (no salta con `http://`).

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

**El código es público; tu contenido es privado y local en cada Mac.**

- Tus snippets viven **solo en este equipo**, en
  `~/Library/Application Support/MechaSnippet/snippets.json`. Es por usuario y por
  Mac: lo que guardes en un computador no viaja a ningún otro.
- **No hay red, ni telemetría, ni nube.** La app no hace una sola conexión: cargar,
  buscar y pegar ocurre 100% en memoria local.
- Tu `snippets.json` real está en `.gitignore`, así que **nunca se sube a GitHub**.
  El repo público solo incluye `snippets.example.json` con **datos ficticios**.
- **No pongas datos reales en `snippets.example.json`** ni hagas commit de un
  `snippets.json` con información sensible.
- El archivo **no está cifrado** (JSON en claro, como casi todos los expansores de
  texto). Queda protegido por tu cuenta de macOS y FileVault. Si quieres
  respaldarlo o sincronizarlo entre tus equipos, hazlo por un canal **privado**
  tuyo (iCloud Drive, un repo privado), nunca por el repo público.

### Cambiar dónde se guarda (opcional)

Si prefieres que este Mac use otra ruta para tu archivo privado, define la
variable de entorno `MECHA_SNIPPET_FILE` (acepta un archivo o una carpeta):

```bash
export MECHA_SNIPPET_FILE="$HOME/Documentos/mis-snippets.json"
python -m mechasnippet
```

Si apuntas a una carpeta, la app usará `snippets.json` dentro de ella. La carpeta
se crea sola si no existe.

## Rendimiento

- Reposo: sin uso de CPU (listener por eventos).
- RAM: del orden de decenas de MB (Python + PyObjC).
- Miles de snippets: carga en memoria una vez y filtro instantáneo; la lista solo
  dibuja las filas visibles.

## Solución de problemas

- **No pasa nada al escribir `//`:** revisa Accesibilidad y Monitoreo de entrada,
  y reinicia la app (el permiso se toma al arrancar).
- **No pega el texto:** confirma el permiso de **Accesibilidad** (necesario para
  enviar `Cmd+V`); es distinto del de Monitoreo de entrada.

## Licencia

MIT. Ver `LICENSE`.
