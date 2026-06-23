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
    private var hotkey: HotkeyMonitor!

    private init() {
        Paths.seedIfNeeded()
        store = SnippetStore(fileURL: Paths.snippetsURL)
        hotkey = HotkeyMonitor { [weak self] in self?.onTrigger() }
        hotkey.start()
    }

    private func onTrigger() {
        guard !paused else { return }
        hotkey.suspended = true
        showPanel()
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

    private func onPanelClose() {
        hotkey.reset()
        hotkey.suspended = false
    }

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

    func showQuickAdd() {
        NSApp.activate(ignoringOtherApps: true)
        quickAddWindow?.close()
        let w = makeWindow(
            title: "Nuevo snippet",
            view: QuickAddView(store: store, onDismiss: { [weak self] in
                self?.quickAddWindow?.close()
            }),
            width: 380, height: 240, resizable: false
        )
        quickAddWindow = w
        w.makeKeyAndOrderFront(nil)
    }

    // Stub completado en tarea 12.
    func showOnboarding() { print("showOnboarding (pendiente)") }

    func togglePause() {
        paused.toggle()
        hotkey.enabled = !paused
    }
    func reload() { store.load() }
}
