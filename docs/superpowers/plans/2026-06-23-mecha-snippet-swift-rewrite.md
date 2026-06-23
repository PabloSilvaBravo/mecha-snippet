# Mecha Snippet 2.0 (Swift) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reescribir Mecha Snippet (expansor de texto de macOS) en Swift nativo, con editor visual de snippets, panel con preview lateral, auto-arranque robusto y onboarding de permisos.

**Architecture:** App de barra de menú (`LSUIElement`) híbrida SwiftUI + AppKit. Lógica pura (modelo, store, matcher) en una librería `MechaSnippetCore` testeable con `swift test`; la UI y los servicios de sistema (NSPanel no-activante, CGEventTap, SMAppService) en el ejecutable `MechaSnippet`. Empaque a `.app` por CLI con un script.

**Tech Stack:** Swift 6.3, SwiftUI (`MenuBarExtra`, `Window`), AppKit (`NSPanel`, `NSHostingView`), CoreGraphics (`CGEventTap`), ServiceManagement (`SMAppService`), Swift Package Manager, `swift-testing`.

## Global Constraints

- **macOS mínimo: 26.0 (Tahoe).** `Package.swift` declara `.macOS(.v26)`.
- **Idioma de toda la UI y copy: español de Chile con tuteo.** Sin voseo. Sin guiones largos en textos de marca.
- **Bundle identifier:** `io.github.pablosilvabravo.mechasnippet`.
- **Nombre visible:** `Mecha Snippet`.
- **Ruta de datos (no cambiar):** `~/Library/Application Support/MechaSnippet/snippets.json`.
- **Datos 100% locales.** Sin red, sin telemetría.
- **Branch de trabajo:** `swift`. No mergear a `main` sin pedir.
- **Firma:** identidad de desarrollo `Apple Development: pablo.silva.bravo.alexa@gmail.com (2PBTW45X92)`.
- **Liquid Glass aislado** en `Glass/GlassBackground.swift` (único punto que toca esa API).
- **Commits granulares** por tarea, en español, terminando con la línea `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

---

### Task 1: Andamio SwiftPM + build verde

**Files:**
- Create: `Package.swift`
- Create: `Sources/MechaSnippetCore/Placeholder.swift`
- Create: `Sources/MechaSnippet/MechaSnippetApp.swift`
- Create: `Sources/MechaSnippet/Resources/snippets.example.json`
- Create: `Scripts/build_app.sh`
- Create: `Scripts/Info.plist.template`

**Interfaces:**
- Produces: ejecutable `MechaSnippet` empaquetable a `dist/Mecha Snippet.app`; librería `MechaSnippetCore` para tareas 2-4.

- [ ] **Step 1: Crear `Package.swift`**

```swift
// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "MechaSnippet",
    platforms: [.macOS(.v26)],
    targets: [
        .target(name: "MechaSnippetCore"),
        .executableTarget(
            name: "MechaSnippet",
            dependencies: ["MechaSnippetCore"],
            resources: [.process("Resources")]
        ),
        .testTarget(
            name: "MechaSnippetCoreTests",
            dependencies: ["MechaSnippetCore"]
        ),
    ]
)
```

- [ ] **Step 2: Placeholder en Core para que compile**

`Sources/MechaSnippetCore/Placeholder.swift`:
```swift
// Reemplazado por Snippet/SnippetStore/Matcher en tareas siguientes.
enum MechaSnippetCore {}
```

- [ ] **Step 3: App mínima con MenuBarExtra**

`Sources/MechaSnippet/MechaSnippetApp.swift`:
```swift
import SwiftUI

@main
struct MechaSnippetApp: App {
    var body: some Scene {
        MenuBarExtra("Mecha Snippet", systemImage: "scissors") {
            Text("Mecha Snippet 2.0")
            Divider()
            Button("Salir") { NSApplication.shared.terminate(nil) }
                .keyboardShortcut("q")
        }
        .menuBarExtraStyle(.menu)
    }
}
```

- [ ] **Step 4: `snippets.example.json` (formato array nuevo)**

`Sources/MechaSnippet/Resources/snippets.example.json`:
```json
[
  {"name": "saludo", "content": "Hola, gracias por escribir a la tienda. ¿En qué te puedo ayudar?"},
  {"name": "despedida", "content": "Quedo atento a cualquier consulta. ¡Que tengas un buen día!"},
  {"name": "correo", "content": "ejemplo@ejemplo.cl"},
  {"name": "pago", "content": "Los datos de transferencia son:\n\nEMPRESA EJEMPLO SPA\nRUT 00.000.000-0\nCta. Corriente Banco Ejemplo N° 00000000\nejemplo@ejemplo.cl"}
]
```

- [ ] **Step 5: Plantilla de Info.plist**

`Scripts/Info.plist.template` (el script reemplaza `__VERSION__`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Mecha Snippet</string>
  <key>CFBundleDisplayName</key><string>Mecha Snippet</string>
  <key>CFBundleIdentifier</key><string>io.github.pablosilvabravo.mechasnippet</string>
  <key>CFBundleExecutable</key><string>MechaSnippet</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleVersion</key><string>__VERSION__</string>
  <key>CFBundleShortVersionString</key><string>__VERSION__</string>
  <key>CFBundleIconFile</key><string>AppIcon</string>
  <key>LSUIElement</key><true/>
  <key>LSMinimumSystemVersion</key><string>26.0</string>
  <key>NSHumanReadableCopyright</key><string>Pablo Silva Bravo</string>
</dict>
</plist>
```

- [ ] **Step 6: `Scripts/build_app.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

VERSION="${1:-2.0.0}"
APP="dist/Mecha Snippet.app"
SIGN_ID="Apple Development: pablo.silva.bravo.alexa@gmail.com (2PBTW45X92)"

echo "==> swift build (release)"
swift build -c release

BIN=".build/release/MechaSnippet"
RES_BUNDLE=".build/release/MechaSnippet_MechaSnippet.bundle"

echo "==> armando $APP"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cp "$BIN" "$APP/Contents/MacOS/MechaSnippet"
[ -d "$RES_BUNDLE" ] && cp -R "$RES_BUNDLE" "$APP/Contents/Resources/"

sed "s/__VERSION__/$VERSION/g" Scripts/Info.plist.template > "$APP/Contents/Info.plist"

# Ícono (si existe el .icns ya generado en la tarea 14)
[ -f "Scripts/AppIcon.icns" ] && cp "Scripts/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"

# LaunchAgent embebido para auto-arranque (lo usa la tarea 11)
[ -f "Scripts/LaunchAgent.plist" ] && {
  mkdir -p "$APP/Contents/Library/LaunchAgents"
  cp "Scripts/LaunchAgent.plist" "$APP/Contents/Library/LaunchAgents/io.github.pablosilvabravo.mechasnippet.plist"
}

echo "==> firmando"
codesign --force --deep --options runtime --sign "$SIGN_ID" "$APP"
codesign --verify --verbose "$APP"
echo "==> listo: $APP"
```

- [ ] **Step 7: Build y verificación**

Run: `chmod +x Scripts/build_app.sh && swift build -c release && ./Scripts/build_app.sh 2.0.0`
Expected: compila sin errores; existe `dist/Mecha Snippet.app`; `codesign --verify` OK.

- [ ] **Step 8: Verificación visual del menubar**

Run: `open "dist/Mecha Snippet.app"` y luego `screencapture -x /tmp/mecha_menubar.png`
Leer `/tmp/mecha_menubar.png`: debe verse el ícono de tijera en la barra de menú. Cerrar: `pkill -f "Mecha Snippet" || true`.

- [ ] **Step 9: Commit**

```bash
git add Package.swift Sources Scripts
git commit -m "feat: andamio SwiftPM + app menubar minima que compila y empaqueta

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Modelo Snippet

**Files:**
- Create: `Sources/MechaSnippetCore/Snippet.swift`
- Delete: `Sources/MechaSnippetCore/Placeholder.swift`
- Test: `Tests/MechaSnippetCoreTests/SnippetTests.swift`

**Interfaces:**
- Produces: `public struct Snippet: Identifiable, Codable, Equatable, Sendable { public var id: UUID; public var name: String; public var content: String; public init(id:name:content:) }`

- [ ] **Step 1: Test que falla**

`Tests/MechaSnippetCoreTests/SnippetTests.swift`:
```swift
import Testing
import Foundation
@testable import MechaSnippetCore

@Test func snippetTieneIdUnicoPorDefecto() {
    let a = Snippet(name: "x", content: "y")
    let b = Snippet(name: "x", content: "y")
    #expect(a.id != b.id)
}

@Test func snippetCodableRoundTrip() throws {
    let s = Snippet(name: "saludo", content: "Hola\ncómo estás")
    let data = try JSONEncoder().encode(s)
    let back = try JSONDecoder().decode(Snippet.self, from: data)
    #expect(back.name == s.name)
    #expect(back.content == s.content)
}
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `swift test --filter SnippetTests`
Expected: FAIL (no existe `Snippet`).

- [ ] **Step 3: Implementar**

`Sources/MechaSnippetCore/Snippet.swift`:
```swift
import Foundation

public struct Snippet: Identifiable, Codable, Equatable, Sendable {
    public var id: UUID
    public var name: String
    public var content: String

    public init(id: UUID = UUID(), name: String, content: String) {
        self.id = id
        self.name = name
        self.content = content
    }
}
```

Borrar `Sources/MechaSnippetCore/Placeholder.swift`.

- [ ] **Step 4: Correr y verificar que pasa**

Run: `swift test --filter SnippetTests`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add Sources/MechaSnippetCore Tests
git commit -m "feat(core): modelo Snippet (Identifiable+Codable) con tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: SnippetStore (lectura 3 formatos + guardado atómico)

**Files:**
- Create: `Sources/MechaSnippetCore/SnippetStore.swift`
- Test: `Tests/MechaSnippetCoreTests/SnippetStoreTests.swift`

**Interfaces:**
- Consumes: `Snippet`.
- Produces:
  - `public final class SnippetStore: ObservableObject { @Published public private(set) var snippets: [Snippet] }`
  - `public init(fileURL: URL)`
  - `public func load()` — lee disco; tolera dict 1.x, lista `{name,content}`, array; si está corrupto conserva memoria.
  - `public func save() throws` — escritura atómica formato array.
  - `public func add(_:)`, `update(_:)`, `delete(id:)`, `move(fromOffsets:toOffset:)` — mutan y guardan.
  - `public static func decode(_ data: Data) -> [Snippet]?` — parser puro de los 3 formatos (nil si no parsea).

- [ ] **Step 1: Tests que fallan**

`Tests/MechaSnippetCoreTests/SnippetStoreTests.swift`:
```swift
import Testing
import Foundation
@testable import MechaSnippetCore

private func tmpURL() -> URL {
    FileManager.default.temporaryDirectory
        .appendingPathComponent("mecha-\(UUID().uuidString).json")
}

@Test func leeFormatoDictLegacy() {
    let json = #"{"saludo":"Hola","pago":"Datos"}"#.data(using: .utf8)!
    let items = SnippetStore.decode(json)!
    #expect(items.count == 2)
    #expect(items.contains { $0.name == "saludo" && $0.content == "Hola" })
}

@Test func leeFormatoListaNameContent() {
    let json = #"[{"name":"a","content":"1"},{"name":"b","content":"2"}]"#.data(using: .utf8)!
    let items = SnippetStore.decode(json)!
    #expect(items.map(\.name) == ["a", "b"])  // preserva orden
}

@Test func jsonCorruptoDevuelveNil() {
    #expect(SnippetStore.decode(Data("{no es json".utf8)) == nil)
}

@Test func guardadoYReloadRoundTrip() throws {
    let url = tmpURL()
    defer { try? FileManager.default.removeItem(at: url) }
    let store = SnippetStore(fileURL: url)
    store.add(Snippet(name: "x", content: "y"))
    let store2 = SnippetStore(fileURL: url)
    store2.load()
    #expect(store2.snippets.map(\.name) == ["x"])
}

@Test func reloadCorruptoConservaMemoria() throws {
    let url = tmpURL()
    defer { try? FileManager.default.removeItem(at: url) }
    let store = SnippetStore(fileURL: url)
    store.add(Snippet(name: "bueno", content: "1"))
    try Data("{roto".utf8).write(to: url)
    store.load()
    #expect(store.snippets.map(\.name) == ["bueno"])  // no se borró
}

@Test func moveReordena() {
    let url = tmpURL()
    defer { try? FileManager.default.removeItem(at: url) }
    let store = SnippetStore(fileURL: url)
    store.add(Snippet(name: "a", content: "1"))
    store.add(Snippet(name: "b", content: "2"))
    store.move(fromOffsets: IndexSet(integer: 1), toOffset: 0)
    #expect(store.snippets.map(\.name) == ["b", "a"])
}
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `swift test --filter SnippetStoreTests`
Expected: FAIL (no existe `SnippetStore`).

- [ ] **Step 3: Implementar**

`Sources/MechaSnippetCore/SnippetStore.swift`:
```swift
import Foundation

public final class SnippetStore: ObservableObject {
    @Published public private(set) var snippets: [Snippet] = []
    public let fileURL: URL

    public init(fileURL: URL) {
        self.fileURL = fileURL
        load()
    }

    public func load() {
        guard let data = try? Data(contentsOf: fileURL) else { return }
        if data.isEmpty { snippets = []; return }
        if let parsed = Self.decode(data) {
            snippets = parsed
        }
        // Si no parsea, se conserva lo que haya en memoria.
    }

    /// Parser puro de los tres formatos aceptados. nil si no es JSON válido.
    public static func decode(_ data: Data) -> [Snippet]? {
        guard let obj = try? JSONSerialization.jsonObject(with: data) else { return nil }
        if let dict = obj as? [String: Any] {
            // Formato 1.x: {"nombre":"contenido"} — orden no garantizado.
            return dict.map { Snippet(name: $0.key, content: String(describing: $0.value)) }
                .sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }
        }
        if let arr = obj as? [[String: Any]] {
            return arr.compactMap { entry in
                guard let name = (entry["name"] ?? entry["key"]) as? String, !name.isEmpty
                else { return nil }
                let content = (entry["content"] ?? entry["value"]) as? String ?? ""
                return Snippet(name: name, content: content)
            }
        }
        return nil
    }

    public func save() throws {
        let payload = snippets.map { ["name": $0.name, "content": $0.content] }
        let data = try JSONSerialization.data(
            withJSONObject: payload, options: [.prettyPrinted, .withoutEscapingSlashes]
        )
        try FileManager.default.createDirectory(
            at: fileURL.deletingLastPathComponent(), withIntermediateDirectories: true
        )
        let tmp = fileURL.deletingLastPathComponent()
            .appendingPathComponent(".\(UUID().uuidString).tmp")
        try data.write(to: tmp, options: .atomic)
        // rename atómico sobre el definitivo
        _ = try FileManager.default.replaceItemAt(fileURL, withItemAt: tmp)
        try? FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: fileURL.path)
    }

    private func persist() { try? save() }

    public func add(_ s: Snippet) { snippets.append(s); persist() }
    public func update(_ s: Snippet) {
        if let i = snippets.firstIndex(where: { $0.id == s.id }) { snippets[i] = s; persist() }
    }
    public func delete(id: UUID) { snippets.removeAll { $0.id == id }; persist() }
    public func move(fromOffsets: IndexSet, toOffset: Int) {
        snippets.move(fromOffsets: fromOffsets, toOffset: toOffset); persist()
    }
}
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `swift test --filter SnippetStoreTests`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add Sources/MechaSnippetCore/SnippetStore.swift Tests
git commit -m "feat(core): SnippetStore con lectura de 3 formatos y guardado atomico

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Matcher (filtrado normalizado + ranking)

**Files:**
- Create: `Sources/MechaSnippetCore/Matcher.swift`
- Test: `Tests/MechaSnippetCoreTests/MatcherTests.swift`

**Interfaces:**
- Consumes: `Snippet`.
- Produces:
  - `public struct Matcher` con `public static func normalize(_:) -> String` (minúsculas, sin tildes).
  - `public static func filter(_ snippets: [Snippet], query: String, normalizedCache: [UUID: (name: String, content: String)]? = nil) -> [Snippet]`.

- [ ] **Step 1: Tests que fallan**

`Tests/MechaSnippetCoreTests/MatcherTests.swift`:
```swift
import Testing
@testable import MechaSnippetCore

private let data = [
    Snippet(name: "saludo", content: "Hola cómo estás"),
    Snippet(name: "pago", content: "datos de transferencia"),
    Snippet(name: "México", content: "envío internacional"),
]

@Test func sinQueryDevuelveTodo() {
    #expect(Matcher.filter(data, query: "").count == 3)
}

@Test func ignoraTildes() {
    #expect(Matcher.filter(data, query: "mexico").map(\.name) == ["México"])
}

@Test func multipalabraExigeTodas() {
    #expect(Matcher.filter(data, query: "datos transferencia").map(\.name) == ["pago"])
    #expect(Matcher.filter(data, query: "datos zzz").isEmpty)
}

@Test func rankingPrefijoNombrePrimero() {
    let items = [
        Snippet(name: "saludo formal", content: "x"),
        Snippet(name: "formal", content: "y"),
    ]
    // "formal" empieza con la query -> va primero
    #expect(Matcher.filter(items, query: "formal").map(\.name) == ["formal", "saludo formal"])
}
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `swift test --filter MatcherTests`
Expected: FAIL (no existe `Matcher`).

- [ ] **Step 3: Implementar**

`Sources/MechaSnippetCore/Matcher.swift`:
```swift
import Foundation

public struct Matcher {
    public static func normalize(_ text: String) -> String {
        text.folding(options: [.diacriticInsensitive, .caseInsensitive], locale: nil)
    }

    public static func filter(
        _ snippets: [Snippet],
        query: String,
        normalizedCache: [UUID: (name: String, content: String)]? = nil
    ) -> [Snippet] {
        let q = normalize(query).trimmingCharacters(in: .whitespaces)
        if q.isEmpty { return snippets }
        let tokens = q.split(separator: " ").map(String.init)

        var scored: [(score: Int, name: String, snippet: Snippet)] = []
        for s in snippets {
            let normName = normalizedCache?[s.id]?.name ?? normalize(s.name)
            let normContent = normalizedCache?[s.id]?.content ?? normalize(s.content)
            let haystack = normName + "\n" + normContent
            guard tokens.allSatisfy({ haystack.contains($0) }) else { continue }

            let score: Int
            if normName.hasPrefix(q) { score = 0 }
            else if normName.contains(q) { score = 1 }
            else if tokens.allSatisfy({ normName.contains($0) }) { score = 2 }
            else { score = 3 }
            scored.append((score, normName, s))
        }
        scored.sort { $0.score != $1.score ? $0.score < $1.score : $0.name < $1.name }
        return scored.map(\.snippet)
    }
}
```

- [ ] **Step 4: Correr y verificar que pasan**

Run: `swift test`
Expected: PASS (todos los tests de Core).

- [ ] **Step 5: Commit**

```bash
git add Sources/MechaSnippetCore/Matcher.swift Tests
git commit -m "feat(core): Matcher con normalizacion sin tildes y ranking, con tests

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: AppState + rutas + cableado del menú

**Files:**
- Create: `Sources/MechaSnippet/Paths.swift`
- Create: `Sources/MechaSnippet/AppState.swift`
- Modify: `Sources/MechaSnippet/MechaSnippetApp.swift`

**Interfaces:**
- Consumes: `SnippetStore`, `Snippet`.
- Produces:
  - `enum Paths { static var snippetsURL: URL; static func seedIfNeeded() }`
  - `final class AppState: ObservableObject { let store: SnippetStore; @Published var paused: Bool; func showPanel(); func showManager(); func showQuickAdd() }` (los métodos se completan en tareas posteriores; aquí stubs que imprimen).

- [ ] **Step 1: Paths**

`Sources/MechaSnippet/Paths.swift`:
```swift
import Foundation

enum Paths {
    static let appDirName = "MechaSnippet"

    static var appSupportDir: URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        let dir = base.appendingPathComponent(appDirName, isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    static var snippetsURL: URL {
        appSupportDir.appendingPathComponent("snippets.json")
    }

    /// Copia el ejemplo embebido la primera vez.
    static func seedIfNeeded() {
        let dest = snippetsURL
        guard !FileManager.default.fileExists(atPath: dest.path) else { return }
        if let example = Bundle.module.url(forResource: "snippets.example", withExtension: "json") {
            try? FileManager.default.copyItem(at: example, to: dest)
        } else {
            try? Data("[]".utf8).write(to: dest)
        }
    }
}
```

- [ ] **Step 2: AppState**

`Sources/MechaSnippet/AppState.swift`:
```swift
import SwiftUI
import MechaSnippetCore

@MainActor
final class AppState: ObservableObject {
    let store: SnippetStore
    @Published var paused = false

    init() {
        Paths.seedIfNeeded()
        store = SnippetStore(fileURL: Paths.snippetsURL)
    }

    // Se implementan en tareas 6, 7, 8.
    func showPanel() { print("showPanel (pendiente)") }
    func showManager() { print("showManager (pendiente)") }
    func showQuickAdd() { print("showQuickAdd (pendiente)") }
    func togglePause() { paused.toggle() }
    func reload() { store.load() }
}
```

- [ ] **Step 3: Cablear el menú**

Reemplazar `Sources/MechaSnippet/MechaSnippetApp.swift`:
```swift
import SwiftUI

@main
struct MechaSnippetApp: App {
    @StateObject private var state = AppState()

    var body: some Scene {
        MenuBarExtra("Mecha Snippet", systemImage: "scissors") {
            Button("Buscar snippet  (//)") { state.showPanel() }
            Divider()
            Button("Nuevo snippet…") { state.showQuickAdd() }
            Button("Gestionar snippets…") { state.showManager() }
            Button("Recargar") { state.reload() }
            Button(state.paused ? "Reanudar detección" : "Pausar detección") { state.togglePause() }
            Divider()
            Button("Salir de Mecha Snippet") { NSApplication.shared.terminate(nil) }
                .keyboardShortcut("q")
        }
        .menuBarExtraStyle(.menu)
    }
}
```

- [ ] **Step 4: Build verde**

Run: `swift build -c release`
Expected: compila sin errores.

- [ ] **Step 5: Verificación visual del menú**

Run: `./Scripts/build_app.sh && open "dist/Mecha Snippet.app"`, abrir el menú de la barra manualmente o `screencapture -x /tmp/mecha_menu.png` con el menú abierto.
Leer la imagen: los ítems del menú aparecen en español. Cerrar app.

- [ ] **Step 6: Commit**

```bash
git add Sources/MechaSnippet
git commit -m "feat: AppState, rutas (Application Support + seed) y menu cableado

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Panel rápido (NSPanel no-activante + preview lateral)

**Files:**
- Create: `Sources/MechaSnippet/Glass/GlassBackground.swift`
- Create: `Sources/MechaSnippet/Panel/SearchPanel.swift`
- Create: `Sources/MechaSnippet/Panel/SearchPanelView.swift`
- Create: `Sources/MechaSnippet/Prefs.swift`
- Modify: `Sources/MechaSnippet/AppState.swift`

**Interfaces:**
- Consumes: `AppState`, `SnippetStore`, `Matcher`.
- Produces:
  - `GlassBackground` (SwiftUI `View` modifier que aplica `.glassEffect` en macOS 26).
  - `final class SearchPanel: NSPanel` con `func present(state:onInsert:)` y memoria de posición vía `Prefs`.
  - `struct SearchPanelView: View` con buscador + lista izquierda + preview derecha; callback `onInsert: (Snippet)->Void`.
  - `enum Prefs { static var panelOrigin: CGPoint? { get set } }` (NSUserDefaults).

- [ ] **Step 1: GlassBackground (aísla Liquid Glass)**

`Sources/MechaSnippet/Glass/GlassBackground.swift`:
```swift
import SwiftUI

/// Fondo Liquid Glass. Único punto que toca esta API: si se baja el target,
/// solo cambia este archivo (fallback a .ultraThinMaterial).
struct GlassBackground: ViewModifier {
    var cornerRadius: CGFloat = 16
    func body(content: Content) -> some View {
        content.background(
            RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                .fill(.clear)
                .glassEffect(in: RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
        )
    }
}

extension View {
    func glassBackground(cornerRadius: CGFloat = 16) -> some View {
        modifier(GlassBackground(cornerRadius: cornerRadius))
    }
}
```

(Si la firma exacta de `.glassEffect` difiere en el SDK 26 instalado, ajustar SOLO aquí; verificar con `swift build`.)

- [ ] **Step 2: Prefs**

`Sources/MechaSnippet/Prefs.swift`:
```swift
import Foundation

enum Prefs {
    private static let originKey = "panelOriginV2"
    static var panelOrigin: CGPoint? {
        get {
            guard let d = UserDefaults.standard.dictionary(forKey: originKey),
                  let x = d["x"] as? Double, let y = d["y"] as? Double else { return nil }
            return CGPoint(x: x, y: y)
        }
        set {
            if let p = newValue {
                UserDefaults.standard.set(["x": p.x, "y": p.y], forKey: originKey)
            } else {
                UserDefaults.standard.removeObject(forKey: originKey)
            }
        }
    }
}
```

- [ ] **Step 3: SearchPanelView (SwiftUI)**

`Sources/MechaSnippet/Panel/SearchPanelView.swift`:
```swift
import SwiftUI
import MechaSnippetCore

struct SearchPanelView: View {
    @ObservedObject var store: SnippetStore
    var onInsert: (Snippet) -> Void
    var onClose: () -> Void

    @State private var query = ""
    @State private var selection: Int = 0
    @FocusState private var searchFocused: Bool

    private var results: [Snippet] { Matcher.filter(store.snippets, query: query) }

    var body: some View {
        VStack(spacing: 8) {
            TextField("Buscar snippet…", text: $query)
                .textFieldStyle(.plain)
                .font(.system(size: 16))
                .focused($searchFocused)
                .onChange(of: query) { selection = 0 }
                .onSubmit { insertCurrent() }

            HStack(alignment: .top, spacing: 10) {
                // Lista izquierda
                ScrollViewReader { proxy in
                    List(selection: Binding(
                        get: { results.indices.contains(selection) ? results[selection].id : nil },
                        set: { id in if let i = results.firstIndex(where: { $0.id == id }) { selection = i } }
                    )) {
                        ForEach(Array(results.enumerated()), id: \.element.id) { i, s in
                            Text(s.name).tag(s.id).id(i)
                                .onTapGesture { selection = i; insertCurrent() }
                        }
                    }
                    .frame(width: 220, height: 260)
                    .scrollContentBackground(.hidden)
                    .onChange(of: selection) { proxy.scrollTo(selection, anchor: .center) }
                }
                // Preview derecha
                ScrollView {
                    Text(results.indices.contains(selection) ? results[selection].content : "")
                        .font(.system(size: 13))
                        .frame(maxWidth: .infinity, alignment: .topLeading)
                        .textSelection(.enabled)
                        .padding(8)
                }
                .frame(width: 320, height: 260)
                .background(.black.opacity(0.04), in: RoundedRectangle(cornerRadius: 10))
            }
        }
        .padding(14)
        .frame(width: 580)
        .glassBackground(cornerRadius: 18)
        .onAppear { searchFocused = true }
        .onKeyPress(.downArrow) { move(1); return .handled }
        .onKeyPress(.upArrow) { move(-1); return .handled }
        .onKeyPress(.escape) { onClose(); return .handled }
    }

    private func move(_ d: Int) {
        guard !results.isEmpty else { return }
        selection = max(0, min(results.count - 1, selection + d))
    }
    private func insertCurrent() {
        guard results.indices.contains(selection) else { return }
        onInsert(results[selection])
    }
}
```

- [ ] **Step 4: SearchPanel (AppKit, no-activante)**

`Sources/MechaSnippet/Panel/SearchPanel.swift`:
```swift
import AppKit
import SwiftUI
import MechaSnippetCore

final class SearchPanel: NSPanel, NSWindowDelegate {
    private var onClose: (() -> Void)?

    init() {
        super.init(
            contentRect: NSRect(x: 0, y: 0, width: 580, height: 320),
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered, defer: false
        )
        isFloatingPanel = true
        level = .floating
        isOpaque = false
        backgroundColor = .clear
        hasShadow = true
        isMovableByWindowBackground = true
        collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        delegate = self
    }

    override var canBecomeKey: Bool { true }
    override var canBecomeMain: Bool { false }

    func present(store: SnippetStore, onInsert: @escaping (Snippet) -> Void, onClose: @escaping () -> Void) {
        self.onClose = onClose
        store.load()
        let root = SearchPanelView(
            store: store,
            onInsert: { [weak self] s in self?.orderOut(nil); onInsert(s) },
            onClose: { [weak self] in self?.close() }
        )
        let host = NSHostingView(rootView: root)
        host.frame = NSRect(x: 0, y: 0, width: 580, height: 320)
        contentView = host
        positionPanel()
        makeKeyAndOrderFront(nil)
    }

    private func positionPanel() {
        let size = NSSize(width: 580, height: 320)
        if let saved = Prefs.panelOrigin {
            setFrameOrigin(saved)
        } else if let screen = NSScreen.main {
            let f = screen.visibleFrame
            setFrameOrigin(NSPoint(x: f.midX - size.width/2, y: f.midY - size.height/2))
        }
    }

    func windowDidMove(_ notification: Notification) {
        Prefs.panelOrigin = frame.origin
    }

    func windowDidResignKey(_ notification: Notification) {
        close()
    }

    override func close() {
        super.close()
        onClose?()
        onClose = nil
    }
}
```

- [ ] **Step 5: Conectar en AppState**

En `AppState.swift`: agregar `private lazy var panel = SearchPanel()` y reemplazar `showPanel()`:
```swift
func showPanel() {
    guard !paused else { return }
    panel.present(
        store: store,
        onInsert: { [weak self] s in self?.insert(s) },
        onClose: { }
    )
}
func insert(_ s: Snippet) { print("insertar: \(s.name)") } // real en tarea 10
```
Importar `AppKit` arriba.

- [ ] **Step 6: Build + verificación visual del panel**

Run: `swift build -c release` (verde) → `./Scripts/build_app.sh && open "dist/Mecha Snippet.app"`. Desde el menú, "Buscar snippet (//)". `screencapture -x /tmp/mecha_panel.png`.
Leer la imagen: panel Liquid Glass centrado, buscador arriba, lista a la izquierda, preview a la DERECHA. Probar flechas/escape manualmente.

- [ ] **Step 7: Commit**

```bash
git add Sources/MechaSnippet
git commit -m "feat: panel rapido NSPanel no-activante con preview lateral y posicion recordada

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Ventana de gestión (CRUD + reordenar arrastrando)

**Files:**
- Create: `Sources/MechaSnippet/Manager/ManagerView.swift`
- Modify: `Sources/MechaSnippet/MechaSnippetApp.swift` (escena `Window`)
- Modify: `Sources/MechaSnippet/AppState.swift` (`showManager`)

**Interfaces:**
- Consumes: `SnippetStore`, `Snippet`.
- Produces: `struct ManagerView: View` (recibe `@ObservedObject store`).

- [ ] **Step 1: ManagerView**

`Sources/MechaSnippet/Manager/ManagerView.swift`:
```swift
import SwiftUI
import MechaSnippetCore

struct ManagerView: View {
    @ObservedObject var store: SnippetStore
    @State private var selectedID: UUID?
    @State private var search = ""

    private var filtered: [Snippet] {
        search.isEmpty ? store.snippets : Matcher.filter(store.snippets, query: search)
    }
    private var selected: Snippet? { store.snippets.first { $0.id == selectedID } }

    var body: some View {
        NavigationSplitView {
            VStack(spacing: 0) {
                HStack {
                    TextField("Buscar…", text: $search).textFieldStyle(.roundedBorder)
                    Button { addNew() } label: { Image(systemName: "plus") }
                }.padding(8)
                List(selection: $selectedID) {
                    ForEach(filtered) { s in
                        VStack(alignment: .leading) {
                            Text(s.name).fontWeight(.medium)
                            Text(s.content.prefix(50)).font(.caption).foregroundStyle(.secondary)
                        }.tag(s.id)
                    }
                    .onMove { from, to in store.move(fromOffsets: from, toOffset: to) }
                }
            }.frame(minWidth: 240)
        } detail: {
            if let sel = selected {
                EditorPane(store: store, snippet: sel)
                    .id(sel.id)
            } else {
                Text("Elige o crea un snippet").foregroundStyle(.secondary)
            }
        }
        .frame(minWidth: 720, minHeight: 460)
        .navigationTitle("Mecha Snippet · Snippets")
    }

    private func addNew() {
        let s = Snippet(name: "nuevo", content: "")
        store.add(s); selectedID = s.id
    }
}

private struct EditorPane: View {
    @ObservedObject var store: SnippetStore
    let snippet: Snippet
    @State private var name = ""
    @State private var content = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            TextField("Nombre", text: $name).textFieldStyle(.roundedBorder).font(.title3)
            TextEditor(text: $content).font(.system(size: 13)).frame(minHeight: 240)
                .overlay(RoundedRectangle(cornerRadius: 6).stroke(.quaternary))
            HStack {
                Button("Duplicar") {
                    store.add(Snippet(name: name + " copia", content: content))
                }
                Spacer()
                Button("Borrar", role: .destructive) { store.delete(id: snippet.id) }
                Button("Guardar") {
                    store.update(Snippet(id: snippet.id, name: name, content: content))
                }.keyboardShortcut("s")
            }
        }
        .padding(16)
        .onAppear { name = snippet.name; content = snippet.content }
    }
}
```

- [ ] **Step 2: Escena Window + openWindow**

En `MechaSnippetApp.swift`, agregar dentro de `body`:
```swift
        Window("Snippets", id: "manager") {
            ManagerView(store: state.store)
        }
        .windowResizability(.contentSize)
```
Y dar a `AppState` acceso a abrir ventanas: en `showManager()` usar `NSApp.activate(ignoringOtherApps: true)` + abrir la escena. Para abrir desde el menú, el botón "Gestionar snippets…" usa `@Environment(\.openWindow)`:
```swift
// en el MenuBarExtra:
@Environment(\.openWindow) var openWindow
...
Button("Gestionar snippets…") { NSApp.activate(ignoringOtherApps: true); openWindow(id: "manager") }
```

- [ ] **Step 3: Build + verificación visual**

Run: `swift build -c release` → empaquetar → abrir → "Gestionar snippets…". `screencapture -x /tmp/mecha_manager.png`.
Leer imagen: lista a la izquierda con buscador y "+", editor a la derecha. Probar agregar, editar+guardar, borrar y arrastrar para reordenar manualmente.

- [ ] **Step 4: Commit**

```bash
git add Sources/MechaSnippet
git commit -m "feat: ventana de gestion con CRUD y reordenar arrastrando

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Mini-formulario "Nuevo snippet"

**Files:**
- Create: `Sources/MechaSnippet/QuickAdd/QuickAddView.swift`
- Modify: `Sources/MechaSnippet/MechaSnippetApp.swift` (escena `Window` id "quickadd")
- Modify: `Sources/MechaSnippet/AppState.swift`

**Interfaces:**
- Consumes: `SnippetStore`.
- Produces: `struct QuickAddView: View`.

- [ ] **Step 1: QuickAddView**

`Sources/MechaSnippet/QuickAdd/QuickAddView.swift`:
```swift
import SwiftUI
import MechaSnippetCore

struct QuickAddView: View {
    @ObservedObject var store: SnippetStore
    @Environment(\.dismiss) private var dismiss
    @State private var name = ""
    @State private var content = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Nuevo snippet").font(.headline)
            TextField("Nombre", text: $name).textFieldStyle(.roundedBorder)
            TextEditor(text: $content).frame(height: 140)
                .overlay(RoundedRectangle(cornerRadius: 6).stroke(.quaternary))
            HStack {
                Spacer()
                Button("Cancelar") { dismiss() }
                Button("Guardar") {
                    let n = name.trimmingCharacters(in: .whitespaces)
                    if !n.isEmpty { store.add(Snippet(name: n, content: content)) }
                    dismiss()
                }.keyboardShortcut(.return).disabled(name.trimmingCharacters(in: .whitespaces).isEmpty)
            }
        }
        .padding(16).frame(width: 380)
    }
}
```

- [ ] **Step 2: Escena + acción de menú**

En `MechaSnippetApp.swift`:
```swift
        Window("Nuevo snippet", id: "quickadd") {
            QuickAddView(store: state.store)
        }
        .windowResizability(.contentSize)
```
Botón del menú: `Button("Nuevo snippet…") { NSApp.activate(ignoringOtherApps: true); openWindow(id: "quickadd") }`.

- [ ] **Step 3: Build + verificación visual**

Run: build → empaquetar → abrir → "Nuevo snippet…". `screencapture -x /tmp/mecha_quickadd.png`. Leer imagen: formulario chico nombre+texto+Guardar. Probar agregar uno y verlo en la gestión.

- [ ] **Step 4: Commit**

```bash
git add Sources/MechaSnippet
git commit -m "feat: mini-formulario Nuevo snippet

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: HotkeyMonitor (CGEventTap detecta "//")

**Files:**
- Create: `Sources/MechaSnippet/Hotkey/HotkeyMonitor.swift`
- Modify: `Sources/MechaSnippet/AppState.swift`

**Interfaces:**
- Produces:
  - `final class HotkeyMonitor { init(onTrigger: @escaping () -> Void); func start(); func stop(); var suspended: Bool; var enabled: Bool; func reset() }`
  - Regla: dispara con dos `/` seguidos; NO dispara si el carácter previo es `:` o `/`.

- [ ] **Step 1: Implementar el tap**

`Sources/MechaSnippet/Hotkey/HotkeyMonitor.swift`:
```swift
import AppKit
import CoreGraphics

final class HotkeyMonitor {
    private let onTrigger: () -> Void
    private var tap: CFMachPort?
    private var runLoopSource: CFRunLoopSource?
    private var recent: [Character] = []

    var enabled = true
    var suspended = false

    init(onTrigger: @escaping () -> Void) { self.onTrigger = onTrigger }

    func start() {
        let mask = (1 << CGEventType.keyDown.rawValue)
        let refcon = Unmanaged.passUnretained(self).toOpaque()
        guard let tap = CGEvent.tapCreate(
            tap: .cgSessionEventTap, place: .headInsertEventTap,
            options: .listenOnly, eventsOfInterest: CGEventMask(mask),
            callback: { _, type, event, refcon in
                if type == .keyDown, let refcon {
                    let me = Unmanaged<HotkeyMonitor>.fromOpaque(refcon).takeUnretainedValue()
                    me.handle(event)
                } else if type == .tapDisabledByTimeout || type == .tapDisabledByUserInput {
                    // El sistema deshabilitó el tap: lo reactivamos.
                    if let refcon {
                        let me = Unmanaged<HotkeyMonitor>.fromOpaque(refcon).takeUnretainedValue()
                        me.reenable()
                    }
                }
                return Unmanaged.passUnretained(event)
            },
            userInfo: refcon
        ) else {
            NSLog("[mecha] no se pudo crear el event tap (¿falta Accesibilidad/Monitoreo?)")
            return
        }
        self.tap = tap
        let src = CFMachPortCreateRunLoopSource(kCFAllocatorDefault, tap, 0)
        self.runLoopSource = src
        CFRunLoopAddSource(CFRunLoopGetMain(), src, .commonModes)
        CGEvent.tapEnable(tap: tap, enable: true)
    }

    private func reenable() { if let tap { CGEvent.tapEnable(tap: tap, enable: true) } }

    func stop() {
        if let tap { CGEvent.tapEnable(tap: tap, enable: false) }
        if let src = runLoopSource { CFRunLoopRemoveSource(CFRunLoopGetMain(), src, .commonModes) }
        tap = nil; runLoopSource = nil
    }

    func reset() { recent.removeAll() }

    private func handle(_ event: CGEvent) {
        guard enabled, !suspended else { return }
        var length = 0
        var chars = [UniChar](repeating: 0, count: 4)
        event.keyboardGetUnicodeString(maxStringLength: 4, actualStringLength: &length, unicodeString: &chars)
        guard length > 0, let scalar = Unicode.Scalar(chars[0]) else { recent.removeAll(); return }
        let ch = Character(scalar)
        if !ch.isLetter && !ch.isNumber && ch != "/" && ch != ":" {
            // separadores varios: no rompemos por espacio, pero sí reiniciamos en raros
        }
        recent.append(ch)
        if recent.count > 3 { recent.removeFirst(recent.count - 3) }

        if recent.count >= 2, recent[recent.count-1] == "/", recent[recent.count-2] == "/" {
            let preceding: Character? = recent.count >= 3 ? recent[recent.count-3] : nil
            if preceding == ":" || preceding == "/" { return }
            recent.removeAll()
            DispatchQueue.main.async { [weak self] in self?.onTrigger() }
        }
    }
}
```

- [ ] **Step 2: Conectar en AppState**

En `AppState.init` (al final): `hotkey = HotkeyMonitor { [weak self] in self?.onTrigger() }; hotkey.start()`. Agregar:
```swift
private var hotkey: HotkeyMonitor!
private func onTrigger() {
    guard !paused else { return }
    hotkey.suspended = true
    showPanel()
}
```
En `togglePause()`: `hotkey.enabled = !paused`. En el `onClose` del panel: `hotkey.reset(); hotkey.suspended = false`.

- [ ] **Step 3: Build + prueba funcional**

Run: build → empaquetar → abrir → conceder permisos si los pide → escribir `//` en otra app (ej. Notas).
Expected: aparece el panel. (Verificación visual: `screencapture` tras teclear `//`.) Confirmar que `http://` NO dispara.

- [ ] **Step 4: Commit**

```bash
git add Sources/MechaSnippet
git commit -m "feat: HotkeyMonitor con CGEventTap (detecta // y se reactiva si el tap muere)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: Inserter (pega y restaura el portapapeles)

**Files:**
- Create: `Sources/MechaSnippet/Hotkey/Inserter.swift`
- Modify: `Sources/MechaSnippet/AppState.swift` (`insert`, reactivar hotkey tras pegar)

**Interfaces:**
- Produces: `enum Inserter { static func insert(_ content: String, backspaces: Int = 2) }`. No borra ni pega si falta Accesibilidad.

- [ ] **Step 1: Implementar**

`Sources/MechaSnippet/Hotkey/Inserter.swift`:
```swift
import AppKit
import CoreGraphics
import ApplicationServices

enum Inserter {
    private static let keyDelete: CGKeyCode = 51
    private static let keyV: CGKeyCode = 9
    private static let concealed = "org.nspasteboard.ConcealedType"
    private static let transient = "org.nspasteboard.TransientType"

    static func insert(_ content: String, backspaces: Int = 2) {
        guard AXIsProcessTrusted() else {
            NSLog("[mecha] sin Accesibilidad: no se pega ni se borra el disparador")
            return
        }
        let pb = NSPasteboard.general
        let saved = snapshot(pb)

        for _ in 0..<backspaces { postKey(keyDelete) }

        pb.clearContents()
        let item = NSPasteboardItem()
        item.setString(content, forType: .string)
        item.setString("", forType: NSPasteboard.PasteboardType(concealed))
        item.setString("", forType: NSPasteboard.PasteboardType(transient))
        pb.writeObjects([item])
        let ourChange = pb.changeCount

        postKey(keyV, flags: .maskCommand)

        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            restore(pb, saved, expected: ourChange)
        }
    }

    private static func postKey(_ code: CGKeyCode, flags: CGEventFlags = []) {
        let src = CGEventSource(stateID: .hidSystemState)
        let down = CGEvent(keyboardEventSource: src, virtualKey: code, keyDown: true)
        let up = CGEvent(keyboardEventSource: src, virtualKey: code, keyDown: false)
        down?.flags = flags; up?.flags = flags
        down?.post(tap: .cghidEventTap); up?.post(tap: .cghidEventTap)
    }

    private static func snapshot(_ pb: NSPasteboard) -> [[NSPasteboard.PasteboardType: Data]] {
        (pb.pasteboardItems ?? []).map { item in
            var d: [NSPasteboard.PasteboardType: Data] = [:]
            for t in item.types { if let data = item.data(forType: t) { d[t] = data } }
            return d
        }
    }

    private static func restore(_ pb: NSPasteboard, _ snap: [[NSPasteboard.PasteboardType: Data]], expected: Int) {
        guard pb.changeCount == expected else { return }  // alguien más lo tocó
        pb.clearContents()
        let items = snap.map { d -> NSPasteboardItem in
            let it = NSPasteboardItem()
            for (t, data) in d { it.setData(data, forType: t) }
            return it
        }
        if !items.isEmpty { pb.writeObjects(items) }
    }
}
```

- [ ] **Step 2: Cablear inserción y rearme del hotkey**

En `AppState`:
```swift
func insert(_ s: Snippet) {
    DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) { [weak self] in
        Inserter.insert(s.content)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            self?.hotkey.reset(); self?.hotkey.suspended = false
        }
    }
}
```

- [ ] **Step 3: Prueba funcional end-to-end**

Run: build → empaquetar → abrir → en Notas escribir `//`, buscar "saludo", Enter.
Expected: se borra el `//` y aparece el texto del snippet; el portapapeles original vuelve a los ~0.5s (copiar algo antes para verificar).

- [ ] **Step 4: Commit**

```bash
git add Sources/MechaSnippet
git commit -m "feat: Inserter pega el snippet y preserva el portapapeles del usuario

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 11: Auto-arranque (SMAppService + LaunchAgent KeepAlive)

**Files:**
- Create: `Sources/MechaSnippet/Launch/LoginItem.swift`
- Create: `Scripts/LaunchAgent.plist`
- Modify: `Sources/MechaSnippet/MechaSnippetApp.swift` (toggle en el menú)

**Interfaces:**
- Produces: `enum LoginItem { static var isEnabled: Bool { get }; static func enable(); static func disable() }` usando `SMAppService.agent(plistName:)`.

- [ ] **Step 1: Plist del agente embebido**

`Scripts/LaunchAgent.plist` (se copia a `Contents/Library/LaunchAgents/` en el build; `BundleProgram` es relativo al bundle):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>io.github.pablosilvabravo.mechasnippet</string>
  <key>BundleProgram</key><string>Contents/MacOS/MechaSnippet</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key>
  <dict><key>SuccessfulExit</key><false/></dict>
  <key>ProcessType</key><string>Interactive</string>
  <key>LimitLoadToSessionType</key><string>Aqua</string>
</dict>
</plist>
```
(`KeepAlive{SuccessfulExit:false}` = revive si se cae con error, pero respeta el "Salir" limpio.)

- [ ] **Step 2: LoginItem**

`Sources/MechaSnippet/Launch/LoginItem.swift`:
```swift
import ServiceManagement

enum LoginItem {
    private static let plistName = "io.github.pablosilvabravo.mechasnippet.plist"
    private static var service: SMAppService { SMAppService.agent(plistName: plistName) }

    static var isEnabled: Bool { service.status == .enabled }

    static func enable() {
        do { try service.register() }
        catch { NSLog("[mecha] no se pudo registrar el Login Item: \(error)") }
    }
    static func disable() {
        do { try service.unregister() }
        catch { NSLog("[mecha] no se pudo quitar el Login Item: \(error)") }
    }
}
```

- [ ] **Step 3: Toggle en el menú**

En `AppState`: `@Published var launchAtLogin = LoginItem.isEnabled` y:
```swift
func toggleLaunchAtLogin() {
    if launchAtLogin { LoginItem.disable() } else { LoginItem.enable() }
    launchAtLogin = LoginItem.isEnabled
}
```
En el `MenuBarExtra`:
```swift
Toggle("Iniciar al abrir sesión", isOn: Binding(
    get: { state.launchAtLogin }, set: { _ in state.toggleLaunchAtLogin() }))
```

- [ ] **Step 4: Build + prueba**

Run: build → empaquetar → mover a `/Applications` (SMAppService exige bundle estable) → abrir → activar "Iniciar al abrir sesión".
Expected: aparece en Ajustes del Sistema > General > Ítems de inicio. `screencapture` del menú con el toggle activo. Verificar `SMAppService` status `.enabled`.

- [ ] **Step 5: Commit**

```bash
git add Sources/MechaSnippet Scripts/LaunchAgent.plist
git commit -m "feat: auto-arranque via SMAppService (agente con KeepAlive) + toggle en el menu

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 12: Permisos + Onboarding

**Files:**
- Create: `Sources/MechaSnippet/Permissions/Permissions.swift`
- Create: `Sources/MechaSnippet/Onboarding/OnboardingView.swift`
- Modify: `Sources/MechaSnippet/MechaSnippetApp.swift` (escena + abrir al inicio si faltan permisos)

**Interfaces:**
- Produces:
  - `enum Permissions { static var accessibility: Bool; static var inputMonitoring: Bool; static func promptAccessibility(); static func openAccessibilitySettings(); static func openInputMonitoringSettings() }`
  - `struct OnboardingView: View`.

- [ ] **Step 1: Permissions**

`Sources/MechaSnippet/Permissions/Permissions.swift`:
```swift
import AppKit
import ApplicationServices
import IOKit.hid

enum Permissions {
    static var accessibility: Bool { AXIsProcessTrusted() }

    static var inputMonitoring: Bool {
        IOHIDCheckAccess(kIOHIDRequestTypeListenEvent) == kIOHIDAccessTypeGranted
    }

    static func promptAccessibility() {
        let opts = [kAXTrustedCheckOptionPrompt.takeUnretainedValue() as String: true]
        _ = AXIsProcessTrustedWithOptions(opts as CFDictionary)
    }

    static func openAccessibilitySettings() {
        open("x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")
    }
    static func openInputMonitoringSettings() {
        open("x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent")
    }
    private static func open(_ s: String) {
        if let url = URL(string: s) { NSWorkspace.shared.open(url) }
    }
}
```

- [ ] **Step 2: OnboardingView**

`Sources/MechaSnippet/Onboarding/OnboardingView.swift`:
```swift
import SwiftUI

struct OnboardingView: View {
    @State private var ax = Permissions.accessibility
    @State private var input = Permissions.inputMonitoring
    private let timer = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Bienvenido a Mecha Snippet").font(.title2).bold()
            Text("Para escuchar el disparador // y pegar texto, macOS pide dos permisos.")
                .foregroundStyle(.secondary)
            row(ok: input, titulo: "Monitoreo de entrada", desc: "para detectar el //") {
                Permissions.openInputMonitoringSettings()
            }
            row(ok: ax, titulo: "Accesibilidad", desc: "para pegar con Cmd+V") {
                Permissions.promptAccessibility(); Permissions.openAccessibilitySettings()
            }
            if ax && input {
                Label("¡Listo! Escribe // en cualquier app.", systemImage: "checkmark.circle.fill")
                    .foregroundStyle(.green)
            }
        }
        .padding(24).frame(width: 460)
        .onReceive(timer) { _ in ax = Permissions.accessibility; input = Permissions.inputMonitoring }
    }

    private func row(ok: Bool, titulo: String, desc: String, action: @escaping () -> Void) -> some View {
        HStack {
            Image(systemName: ok ? "checkmark.circle.fill" : "circle")
                .foregroundStyle(ok ? .green : .secondary)
            VStack(alignment: .leading) {
                Text(titulo).fontWeight(.medium)
                Text(desc).font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            if !ok { Button("Conceder", action: action) }
        }
    }
}
```

- [ ] **Step 3: Escena + abrir al inicio si faltan permisos**

En `MechaSnippetApp.swift`:
```swift
        Window("Bienvenido", id: "onboarding") { OnboardingView() }
            .windowResizability(.contentSize)
```
Y un `Button("Permisos y bienvenida…")` en el menú. En `AppState.init`, si `!Permissions.accessibility || !Permissions.inputMonitoring`, marcar una bandera para que la app abra "onboarding" al primer arranque (vía `openWindow` desde un `.onAppear` o `NSApp`).

- [ ] **Step 4: Build + verificación visual**

Run: build → empaquetar → abrir. `screencapture` de la ventana de bienvenida.
Leer imagen: dos filas (Monitoreo / Accesibilidad) con su estado y botón "Conceder"; el check verde aparece al conceder.

- [ ] **Step 5: Commit**

```bash
git add Sources/MechaSnippet
git commit -m "feat: onboarding de permisos (Accesibilidad + Monitoreo) con deteccion en vivo

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 13: Pulido visual + jerarquía

**Files:**
- Modify: `Sources/MechaSnippet/Panel/SearchPanelView.swift`
- Modify: `Sources/MechaSnippet/Manager/ManagerView.swift`

**Interfaces:** sin cambios de API; solo presentación.

- [ ] **Step 1: Pulir el panel**

Mejorar `SearchPanelView`: nombre del snippet en `.medium`, fila seleccionada resaltada, preview con `lineSpacing(2)`, placeholder y márgenes consistentes, estado vacío ("Sin resultados"). Mantener el `.glassBackground`.

- [ ] **Step 2: Pulir la gestión**

Iconos en los botones, contador de snippets en el título, estado vacío con llamada a "+ Nuevo".

- [ ] **Step 3: Build + verificación visual comparativa**

Run: build → empaquetar → abrir. `screencapture` del panel y de la gestión. Leer ambas imágenes y confirmar jerarquía/legibilidad. Ajustar si algo se ve apretado o desalineado.

- [ ] **Step 4: Commit**

```bash
git add Sources/MechaSnippet
git commit -m "style: pulido visual del panel y la gestion (jerarquia, estados vacios)

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 14: Ícono, DMG, README y release

**Files:**
- Create: `Scripts/make_icon.sh`, `Scripts/AppIcon.icns` (generado)
- Create: `Scripts/make_dmg.sh`
- Modify: `README.md`
- Create: `Sources/MechaSnippet/Resources/icon-source.png` (1024×1024)

**Interfaces:** entrega `dist/Mecha Snippet.app` con ícono + `dist/MechaSnippet-2.0.0.dmg`.

- [ ] **Step 1: Generar el ícono**

Crear `icon-source.png` (1024×1024, marca tijera/Mecha). `Scripts/make_icon.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
SRC="Sources/MechaSnippet/Resources/icon-source.png"
ICONSET="$(mktemp -d)/AppIcon.iconset"; mkdir -p "$ICONSET"
for s in 16 32 128 256 512; do
  sips -z $s $s "$SRC" --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
  sips -z $((s*2)) $((s*2)) "$SRC" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o Scripts/AppIcon.icns
echo "==> Scripts/AppIcon.icns generado"
```

- [ ] **Step 2: make_dmg.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
VERSION="${1:-2.0.0}"
APP="dist/Mecha Snippet.app"
DMG="dist/MechaSnippet-$VERSION.dmg"
STAGING="$(mktemp -d)"
cp -R "$APP" "$STAGING/"
ln -s /Applications "$STAGING/Applications"
rm -f "$DMG"
hdiutil create -volname "Mecha Snippet" -srcfolder "$STAGING" -ov -format UDZO "$DMG"
echo "==> $DMG"
```

- [ ] **Step 3: Generar todo y verificar**

Run: `chmod +x Scripts/*.sh && ./Scripts/make_icon.sh && ./Scripts/build_app.sh 2.0.0 && ./Scripts/make_dmg.sh 2.0.0`
Expected: `.app` con ícono propio (verificar en Finder con `screencapture`) y `.dmg` creado. Abrir el DMG y confirmar el layout (app + alias a Applications).

- [ ] **Step 4: Actualizar README**

Reescribir `README.md`: badges, "Descargar DMG", requisitos (macOS 26+), features 2.0 (editor visual, preview lateral, auto-arranque, onboarding), sección de desarrollo (`swift build`, `./Scripts/build_app.sh`), formato de `snippets.json` (array), privacidad. Español de Chile, sin guiones largos en copy.

- [ ] **Step 5: Commit**

```bash
git add Scripts README.md Sources/MechaSnippet/Resources/icon-source.png
git commit -m "build: icono propio, DMG, README 2.0 y empaque de release

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 6: Verificación final end-to-end**

Lista de chequeo manual (marcar cada una):
- [ ] `//` abre el panel en cualquier app; `http://` no.
- [ ] Buscar + flechas + Enter pega el snippet correcto.
- [ ] El portapapeles original se restaura tras pegar.
- [ ] El panel recuerda su posición al moverlo.
- [ ] Gestión: agregar / editar / borrar / duplicar / reordenar arrastrando persisten.
- [ ] Mini-formulario agrega un snippet.
- [ ] "Iniciar al abrir sesión" registra el Login Item.
- [ ] Onboarding refleja permisos en vivo.
- [ ] `swift test` en verde.
- [ ] App firmada (`codesign --verify`).

---

## Self-Review

**Cobertura del spec:**
- Editor (ventana + mini-formulario) → Tasks 7, 8. ✓
- Panel preview lateral + posición recordada + reordenar → Tasks 6 (panel), 7 (reordenar en gestión). ✓
- Auto-arranque Login Item + revivir → Task 11. ✓
- Onboarding → Task 12. ✓
- Rendimiento (normalización precomputada) → Task 4 (Matcher con caché opcional; List perezosa en 6/7). ✓
- Empaque/ícono/DMG/README → Tasks 1 (build), 14. ✓
- Lectura 3 formatos + guardado atómico → Task 3. ✓
- Liquid Glass aislado → Task 6 (`GlassBackground`). ✓
- Hotkey + inserción con preservación de portapapeles → Tasks 9, 10. ✓

**Sin placeholders:** todos los pasos de código traen el código. (La caché de normalización del Matcher es un parámetro opcional ya implementado; si el perfilado lo pide, se llena desde el store, sin cambiar la firma.)

**Consistencia de tipos:** `SnippetStore.move(fromOffsets:toOffset:)` usado igual en Task 3 y Task 7. `Matcher.filter(_:query:normalizedCache:)` igual en 4, 6, 7. `AppState.showPanel/showManager/showQuickAdd/insert` declarados en 5 y completados en 6/7/8/10. `LoginItem.isEnabled/enable/disable` consistente en 11. ✓
