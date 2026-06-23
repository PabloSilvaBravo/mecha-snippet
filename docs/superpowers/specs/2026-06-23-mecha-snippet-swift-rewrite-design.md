# Mecha Snippet 2.0 — Reescritura nativa en Swift

**Fecha:** 2026-06-23
**Autor:** Pablo Silva Bravo (con Claude)
**Estado:** Aprobado para implementación
**Branch:** `swift`

## Contexto

Mecha Snippet es un expansor de texto para macOS: escribes `//` en cualquier app,
aparece un panel flotante, buscas un snippet y lo pegas. La versión 1.x está escrita
en Python + PyObjC (`mechasnippet/`, ~1.150 líneas), empaquetada con py2app, con un
release `v1.0.0` publicado en GitHub (`PabloSilvaBravo/mecha-snippet`).

Esta reescritura (2.0) reemplaza la base Python por **Swift nativo** para lograr una
app más liviana, robusta y vistosa, apta para distribución pública. El objetivo de
producto es que la gente la descargue y la use.

## Objetivo

Reescribir Mecha Snippet en Swift nativo, conservando el comportamiento central
(disparador `//`, panel de búsqueda, pegado con preservación del portapapeles) y
sumando lo que la 1.x no tiene:

1. Editor visual de snippets (ventana de gestión + mini-formulario), sin tocar JSON a mano.
2. Panel rediseñado: preview a la derecha, posición recordada, reordenamiento.
3. Auto-arranque robusto (Login Item nativo + revivir si se cae).
4. Onboarding de permisos en la primera corrida.
5. Rendimiento que escale a miles de snippets.
6. Empaque profesional (ícono propio, firma, DMG).

## Decisiones tomadas (brainstorming)

| Tema | Decisión |
|---|---|
| Lenguaje | Swift 6 (reescritura total; se descarta la base Python) |
| UI | SwiftUI para vistas internas + AppKit para `NSPanel` no-activante y `CGEventTap` |
| macOS mínimo | **macOS 26 Tahoe** (Liquid Glass nativo pleno) |
| Layout panel | Preview del texto completo **a la derecha** de la lista |
| Panel | Movible y **recuerda su posición** entre aperturas |
| Reordenar | **Arrastrando** en la ventana de gestión |
| Editor | **Ventana de gestión completa** + **mini-formulario "Nuevo snippet"** |
| Auto-arranque | **Login Item (SMAppService)** + KeepAlive (revive si se cae) |
| Distribución | Onboarding pulido, **sin notarizar** por ahora (firma de desarrollo) |
| Build | Swift Package Manager + script de empaquetado por CLI |
| Repo | Branch `swift`; `main` (Python) queda intacto hasta terminar |

**Nota sobre el target macOS 26:** reduce la audiencia a corto plazo (poca gente tiene
Tahoe). Se acepta a cambio del Liquid Glass nativo y código más simple. El código se
escribe de modo que bajar el target a Ventura más adelante sea un cambio acotado
(efectos de cristal aislados tras un punto de extensión, no esparcidos por la UI).

## Entorno verificado

- macOS 26.5.1 (Tahoe), Apple Silicon (arm64)
- Swift 6.3.2, Xcode 26.5 completo (permite `swift build` y `xcodebuild` por CLI)
- Identidad de firma de desarrollo disponible
  (`Apple Development: pablo.silva.bravo.alexa@gmail.com`) — sirve para firmar y
  registrar el Login Item; **no** es Developer ID (no habilita notarización).

## Arquitectura

App de barra de menú (`LSUIElement`, sin Dock). Híbrido SwiftUI + AppKit.

```
Sources/MechaSnippet/
├── MechaSnippetApp.swift        @main; MenuBarExtra; AppDelegate; cableado
├── AppState.swift               ObservableObject central (store, pausa, prefs)
├── Models/
│   └── Snippet.swift            struct Snippet: Identifiable, Codable {id,name,content}
├── Store/
│   └── SnippetStore.swift       carga/guardado ATÓMICO del JSON; @Published items
├── Search/
│   └── Matcher.swift            filtrado normalizado (precomputado) + ranking
├── Hotkey/
│   ├── HotkeyMonitor.swift      CGEventTap detecta "//"; auto-reinicio si muere
│   └── Inserter.swift           NSPasteboard + Cmd+V; preserva el portapapeles
├── Panel/
│   ├── SearchPanel.swift        NSPanel no-activante (AppKit) que hostea SwiftUI
│   └── SearchPanelView.swift    SwiftUI: buscador + lista + preview lateral
├── Manager/
│   └── ManagerView.swift        SwiftUI: gestión completa + drag-to-reorder
├── QuickAdd/
│   └── QuickAddView.swift       SwiftUI: mini-formulario "Nuevo snippet"
├── Onboarding/
│   └── OnboardingView.swift     SwiftUI: guía de permisos
├── Launch/
│   └── LoginItem.swift          SMAppService: registrar/estado/KeepAlive
├── Permissions/
│   └── Permissions.swift        chequeo Accesibilidad / Monitoreo de entrada
├── Glass/
│   └── GlassBackground.swift    punto único de efecto Liquid Glass (aísla la API)
└── Resources/
    ├── snippets.example.json
    └── Assets.xcassets/AppIcon
Scripts/
├── build_app.sh                 swift build -c release → .app + Info.plist + firma
└── make_dmg.sh                  empaqueta el DMG de release
```

### Unidades y responsabilidades

- **Snippet** — modelo de datos puro. `id: UUID` (en memoria, para SwiftUI/drag),
  `name: String`, `content: String`.
- **SnippetStore** — única fuente de verdad de los snippets. Carga desde disco,
  guarda de forma atómica, expone `@Published [Snippet]`. API:
  `load()`, `add`, `update`, `delete`, `move(from:to:)`, `reload()`. No conoce UI.
- **Matcher** — función pura: `filter(_ snippets:, query:) -> [Snippet]`. Normaliza
  (minúsculas, sin tildes) una sola vez por snippet (precomputado en el store o en una
  caché), no por tecla. Testeable sin UI.
- **HotkeyMonitor** — envuelve un `CGEventTap`. Detecta `//` con la misma regla que la
  1.x (no dispara tras `:` ni `/`, para no saltar en URLs ni en `///`). Despacha al main
  thread. Se puede pausar/reanudar y se reinicia solo si el tap se invalida.
- **Inserter** — pega el snippet: snapshot completo del portapapeles (todos los tipos),
  backspaces para borrar el `//`, escribe el snippet marcado como efímero
  (`org.nspasteboard.ConcealedType`/`TransientType`), envía Cmd+V y restaura el
  portapapeles si nadie más lo tocó (chequeo de `changeCount`).
- **SearchPanel** — `NSPanel` borderless, `.nonactivatingPanel`, nivel flotante,
  `canBecomeKey = true`. Hostea `SearchPanelView` vía `NSHostingView`. Gestiona mostrar/
  ocultar, recordar posición y cerrar al perder el foco o con Esc.
- **SearchPanelView** — SwiftUI. Campo de búsqueda arriba, lista a la izquierda, preview
  del contenido completo a la derecha (wrapping flexible). Navegación ↑/↓, Enter pega.
- **ManagerView** — SwiftUI en una `Window` normal. Lista editable con búsqueda,
  agregar/borrar/duplicar, edición de nombre y contenido, reordenamiento por arrastre.
- **QuickAddView** — SwiftUI. Formulario mínimo (nombre + contenido) para sumar un
  snippet rápido sin abrir la gestión.
- **OnboardingView** — SwiftUI. Detecta permisos faltantes y guía a concederlos con
  botones que abren el panel exacto de Ajustes del Sistema; detecta cuando se otorgan.
- **LoginItem** — envuelve `SMAppService`. Registrar/desregistrar, leer estado para el
  toggle del menú. Estrategia KeepAlive para que reviva si se cae.
- **Permissions** — helpers: ¿hay Accesibilidad? (`AXIsProcessTrusted`), ¿hay Monitoreo
  de entrada? Abrir los paneles de Ajustes correspondientes.
- **GlassBackground** — único lugar que toca la API de Liquid Glass. Si mañana se baja
  el target, solo cambia este archivo.

## Flujo de datos

1. Al arrancar: `SnippetStore.load()` lee el JSON (crea uno desde el ejemplo si no
   existe). `AppState` queda con los snippets en memoria.
2. `HotkeyMonitor` detecta `//` → notifica a `AppState` → se muestra el `SearchPanel`.
3. El usuario teclea → `SearchPanelView` filtra vía `Matcher` (sobre datos en memoria).
4. Enter → `SearchPanel` se oculta, reactiva la app previa, `Inserter` borra el `//` y
   pega el snippet, luego restaura el portapapeles.
5. La gestión y el mini-formulario mutan el `SnippetStore`, que guarda atómicamente y
   publica el cambio; el panel ve los datos nuevos en la próxima apertura.

## Formato de datos

- Ruta (sin cambios respecto a la 1.x): `~/Library/Application Support/MechaSnippet/snippets.json`.
  Garantiza que un usuario que venía de la 1.x conserve sus snippets.
- **Escritura canónica:** array JSON con orden explícito:
  ```json
  [
    {"name": "saludo", "content": "Hola, ¿en qué te ayudo?"},
    {"name": "pago", "content": "Datos de transferencia:\n..."}
  ]
  ```
- **Lectura retrocompatible:** se acepta también el formato dict de la 1.x
  (`{"nombre": "contenido"}`) y la lista de `{name, content}`. Al primer guardado desde
  la app, el archivo se reescribe en formato array.
- **Atomicidad:** escribir a un archivo temporal en la misma carpeta y `rename` sobre el
  definitivo, para no corromper el JSON ante un fallo a mitad de escritura. Permisos
  `0600` (privado).

## Manejo de errores

- **JSON corrupto al recargar:** conservar la última versión buena en memoria (igual que
  la 1.x) y avisar de forma visible (no solo a stderr).
- **Sin Accesibilidad al pegar:** no borrar el `//` ni tocar el portapapeles (para no
  comerse texto); en su lugar, abrir/destacar el onboarding.
- **Event tap invalidado** (macOS puede deshabilitarlo): detectarlo y recrear el tap.
- **Fallo al guardar** (disco lleno, permisos): mantener los datos en memoria y mostrar
  el error; no perder lo que el usuario escribió.
- **Login Item rechazado** por el sistema: reflejar el estado real en el toggle, no
  asumir éxito.

## Rendimiento

- Normalización (minúsculas + sin tildes) **precomputada** una vez por snippet, no por
  tecla. Filtrar miles de entradas por pulsación queda barato.
- Lista del panel y de la gestión con renderizado perezoso de SwiftUI (`List`/`LazyVStack`).
- Cálculo de ancho del panel acotado/cacheado; pequeño debounce al teclear si hace falta.
- Objetivo: fluido con ≥ 5.000 snippets.

## Empaque y distribución

- `Scripts/build_app.sh`: `swift build -c release`, arma
  `Mecha Snippet.app/Contents/{MacOS,Resources,Library/LaunchAgents}`, escribe el
  `Info.plist` (`LSUIElement`, `CFBundleIdentifier io.github.pablosilvabravo.mechasnippet`,
  versión), copia `AppIcon.icns`, y firma con la identidad de desarrollo.
- `Scripts/make_dmg.sh`: genera el DMG de release (con `hdiutil`; sin dependencias extra).
- Ícono de app propio (reemplaza el default).
- README y release nuevos cuando la app esté verificada.

## Testing

- **Unit (sin UI), donde está el valor:**
  - `Matcher`: ranking, sin tildes, multipalabra, sin query, sin resultados.
  - `SnippetStore`: lectura de los tres formatos (dict 1.x, lista, array), guardado
    atómico, round-trip, resiliencia ante JSON corrupto, migración de formato.
- **Manual/visual (app de escritorio):** en cada fase de UI, lanzar la app, capturar la
  pantalla con `screencapture`, revisar la imagen y mostrarla antes de declarar la fase
  lista. Disparar el panel/ventanas por un modo de depuración para poder capturarlos.

## Plan de implementación (fases para el loop)

1. **Andamio + build verde** — `Package.swift`, `MenuBarExtra` mínimo, `build_app.sh`
   que compile, empaque y firme un `.app` que aparezca en la barra de menú.
2. **Núcleo de datos** — `Snippet`, `SnippetStore` (3 formatos + guardado atómico),
   `Matcher`; tests unitarios en verde.
3. **Panel rápido** — `SearchPanel` (NSPanel no-activante) + `SearchPanelView`
   (preview lateral, flechas, posición recordada).
4. **Gestión + mini-formulario** — `ManagerView` (CRUD + drag-to-reorder) y `QuickAddView`.
5. **Hotkey + inserción** — `HotkeyMonitor` (CGEventTap) e `Inserter` (pegado + restauración).
6. **Auto-arranque** — `LoginItem` (SMAppService + KeepAlive) + toggle en el menú.
7. **Onboarding** — `OnboardingView` + helpers de `Permissions`.
8. **Pulido + empaque** — ícono, `make_dmg.sh`, README, verificación visual final.

Cada fase termina con build verde, verificación (tests o captura visual) y commit granular.

## Fuera de alcance (YAGNI por ahora)

- Notarización con Apple (requiere Developer ID de pago).
- Sincronización en la nube de los snippets (sigue siendo 100% local).
- Captura rápida desde la selección de texto en otra app (no fue elegida).
- Soporte de macOS anterior a Tahoe (el código deja la puerta abierta, pero no se implementa).
- Migración del proyecto a Mac App Store.
