import SwiftUI
import AppKit
import MechaSnippetCore

@MainActor
final class AppState: ObservableObject {
    static let shared = AppState()

    let store: SnippetStore
    @Published var paused = false

    private lazy var panel = SearchPanel()

    private init() {
        Paths.seedIfNeeded()
        store = SnippetStore(fileURL: Paths.snippetsURL)
    }

    func showPanel() {
        guard !paused else { return }
        panel.present(
            store: store,
            onInsert: { [weak self] s in self?.insert(s) },
            onClose: { [weak self] in self?.onPanelClose() }
        )
    }

    // Real en tarea 10 (Inserter). Por ahora solo registra.
    func insert(_ s: Snippet) { print("insertar: \(s.name)") }

    // Real en tarea 9 (rearme del hotkey). Por ahora no-op.
    private func onPanelClose() {}

    // Stubs completados en tareas 7, 8, 12.
    func showManager() { print("showManager (pendiente)") }
    func showQuickAdd() { print("showQuickAdd (pendiente)") }
    func showOnboarding() { print("showOnboarding (pendiente)") }

    func togglePause() { paused.toggle() }
    func reload() { store.load() }
}
