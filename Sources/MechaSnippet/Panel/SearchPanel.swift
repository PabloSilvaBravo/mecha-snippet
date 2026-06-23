import AppKit
import SwiftUI
import MechaSnippetCore

/// Panel flotante no-activante que hostea la vista de búsqueda. No le roba la
/// activación a la app de fondo (para que el pegado vuelva solo a su lugar).
/// El teclado (flechas, Enter, Esc) se maneja con un monitor de eventos local.
final class SearchPanel: NSPanel, NSWindowDelegate {
    private var model: PanelModel?
    private var keyMonitor: Any?
    private var onCloseCallback: (() -> Void)?
    private var ignoreResign = false

    init() {
        super.init(
            contentRect: NSRect(x: 0, y: 0, width: 600, height: 360),
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

    func present(
        store: SnippetStore,
        onInsert: @escaping (Snippet) -> Void,
        onClose: @escaping () -> Void
    ) {
        store.load()
        let model = PanelModel(store: store)
        model.resetForShow()
        // Al insertar NO rearmamos el hotkey en el cierre: lo hace insert() después
        // de pegar, para que el Cmd+V sintético no reactive la detección de '//'.
        model.onInsert = { [weak self] s in self?.dismiss(callClose: false); onInsert(s) }
        model.onClose = { [weak self] in self?.dismiss(callClose: true) }
        self.model = model
        self.onCloseCallback = onClose

        let host = NSHostingView(rootView: SearchPanelView(model: model))
        contentView = host
        setContentSize(host.fittingSize)
        positionPanel()
        installKeyMonitor()
        makeKeyAndOrderFront(nil)
    }

    private func positionPanel() {
        let size = frame.size
        if let saved = Prefs.panelOrigin {
            setFrameOrigin(saved)
        } else if let screen = NSScreen.main {
            let f = screen.visibleFrame
            setFrameOrigin(NSPoint(x: f.midX - size.width / 2, y: f.midY - size.height / 2))
        }
    }

    private func installKeyMonitor() {
        keyMonitor = NSEvent.addLocalMonitorForEvents(matching: .keyDown) { [weak self] event in
            guard let self, let model = self.model else { return event }
            switch event.keyCode {
            case 125: model.move(1); return nil       // ↓
            case 126: model.move(-1); return nil      // ↑
            case 36, 76: model.insertCurrent(); return nil  // Return / Enter
            case 53: model.onClose(); return nil      // Esc
            default: return event
            }
        }
    }

    func dismiss(callClose: Bool = true) {
        if let m = keyMonitor { NSEvent.removeMonitor(m); keyMonitor = nil }
        ignoreResign = true
        orderOut(nil)
        ignoreResign = false
        model = nil
        let cb = onCloseCallback
        onCloseCallback = nil
        if callClose { cb?() }
    }

    // Guardar la posición al moverlo.
    func windowDidMove(_ notification: Notification) {
        if isVisible { Prefs.panelOrigin = frame.origin }
    }

    // Cerrar al perder el foco (click fuera).
    func windowDidResignKey(_ notification: Notification) {
        guard !ignoreResign, isVisible else { return }
        model?.onClose()
    }
}
