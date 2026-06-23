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
