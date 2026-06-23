import SwiftUI

@main
struct MechaSnippetApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate
    @StateObject private var state = AppState.shared

    var body: some Scene {
        MenuBarExtra("Mecha Snippet", systemImage: "scissors") {
            Button("Buscar snippet  (//)") { state.showPanel() }
            Divider()
            Button("Nuevo snippet…") { state.showQuickAdd() }
            Button("Gestionar snippets…") { state.showManager() }
            Button("Recargar") { state.reload() }
            Button(state.paused ? "Reanudar detección" : "Pausar detección") { state.togglePause() }
            Toggle("Iniciar al abrir sesión", isOn: Binding(
                get: { state.launchAtLogin },
                set: { _ in state.toggleLaunchAtLogin() }
            ))
            Divider()
            Button("Salir de Mecha Snippet") { NSApplication.shared.terminate(nil) }
                .keyboardShortcut("q")
        }
        .menuBarExtraStyle(.menu)
    }
}
