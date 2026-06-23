import SwiftUI
import AppKit
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
