import SwiftUI
import AppKit
import MechaSnippetCore

@MainActor
final class AppState: ObservableObject {
    static let shared = AppState()

    let store: SnippetStore
    @Published var paused = false

    private lazy var panel = SearchPanel()
    private var managerWindow: NSWindow?
    private var quickAddWindow: NSWindow?
    private var onboardingWindow: NSWindow?

    private init() {
        Paths.seedIfNeeded()
        store = SnippetStore(fileURL: Paths.snippetsURL)
    }

    /// Crea (o reusa) una NSWindow que hostea una vista SwiftUI. Permite abrir
    /// las ventanas programáticamente desde el menú o los disparadores de debug.
    private func makeWindow<V: View>(
        title: String, view: V, width: CGFloat, height: CGFloat, resizable: Bool
    ) -> NSWindow {
        let style: NSWindow.StyleMask = resizable
            ? [.titled, .closable, .miniaturizable, .resizable]
            : [.titled, .closable]
        let w = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: width, height: height),
            styleMask: style, backing: .buffered, defer: false
        )
        w.title = title
        w.contentView = NSHostingView(rootView: view)
        w.center()
        w.isReleasedWhenClosed = false
        return w
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

    func showManager() {
        NSApp.activate(ignoringOtherApps: true)
        if managerWindow == nil {
            managerWindow = makeWindow(
                title: "Mecha Snippet", view: ManagerView(store: store),
                width: 760, height: 480, resizable: true
            )
        }
        managerWindow?.makeKeyAndOrderFront(nil)
    }

    // Stubs completados en tareas 8, 12.
    func showQuickAdd() { print("showQuickAdd (pendiente)") }
    func showOnboarding() { print("showOnboarding (pendiente)") }

    func togglePause() { paused.toggle() }
    func reload() { store.load() }
}
