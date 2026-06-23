import SwiftUI
import AppKit
import MechaSnippetCore

@MainActor
final class AppState: ObservableObject {
    static let shared = AppState()

    let store: SnippetStore
    @Published var paused = false
    @Published var launchAtLogin = LoginItem.isEnabled

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

    /// Pega tras un pequeño retardo (para que el foco vuelva a la app anterior) y
    /// RECIÉN AHÍ reactiva el listener, para que el Cmd+V sintético no reactive la
    /// detección de '//' ni se coma el próximo disparador.
    func insert(_ s: Snippet) {
        let content = s.content
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) { [weak self] in
            Inserter.insert(content)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
                self?.hotkey.reset()
                self?.hotkey.suspended = false
            }
        }
    }

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

    func showOnboarding() {
        NSApp.activate(ignoringOtherApps: true)
        if onboardingWindow == nil {
            onboardingWindow = makeWindow(
                title: "Bienvenido a Mecha Snippet", view: OnboardingView(),
                width: 480, height: 380, resizable: false
            )
        }
        onboardingWindow?.makeKeyAndOrderFront(nil)
    }

    /// True si falta algún permiso (para mostrar el onboarding al arrancar).
    var needsPermissions: Bool {
        !Permissions.accessibility || !Permissions.inputMonitoring
    }

    func togglePause() {
        paused.toggle()
        hotkey.enabled = !paused
    }

    func toggleLaunchAtLogin() {
        if launchAtLogin { LoginItem.disable() } else { LoginItem.enable() }
        launchAtLogin = LoginItem.isEnabled
    }

    func reload() { store.load() }
}
