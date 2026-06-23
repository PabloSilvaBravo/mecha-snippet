import AppKit
import CoreGraphics

/// Escucha global del teclado vía CGEventTap para detectar el disparador "//".
/// El tap se instala en el run loop principal, así que todo su estado se toca
/// solo desde el main thread (por eso @unchecked Sendable es seguro aquí).
final class HotkeyMonitor: @unchecked Sendable {
    private let onTrigger: @MainActor () -> Void
    private var tap: CFMachPort?
    private var runLoopSource: CFRunLoopSource?
    private var recent: [Character] = []

    var enabled = true       // interruptor global (menú Pausar)
    var suspended = false    // true mientras el panel está visible

    init(onTrigger: @escaping @MainActor () -> Void) {
        self.onTrigger = onTrigger
    }

    func start() {
        let mask = CGEventMask(1 << CGEventType.keyDown.rawValue)
        let refcon = Unmanaged.passUnretained(self).toOpaque()

        guard let tap = CGEvent.tapCreate(
            tap: .cgSessionEventTap,
            place: .headInsertEventTap,
            options: .defaultTap,
            eventsOfInterest: mask,
            callback: { _, type, event, refcon in
                guard let refcon else { return Unmanaged.passUnretained(event) }
                let me = Unmanaged<HotkeyMonitor>.fromOpaque(refcon).takeUnretainedValue()
                if type == .keyDown {
                    me.handle(event)
                } else if type == .tapDisabledByTimeout || type == .tapDisabledByUserInput {
                    me.reenable()  // el sistema deshabilitó el tap: lo reactivamos
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

    var isActive: Bool { tap != nil }

    private func reenable() {
        if let tap { CGEvent.tapEnable(tap: tap, enable: true) }
    }

    func stop() {
        if let tap { CGEvent.tapEnable(tap: tap, enable: false) }
        if let src = runLoopSource { CFRunLoopRemoveSource(CFRunLoopGetMain(), src, .commonModes) }
        tap = nil
        runLoopSource = nil
    }

    func reset() { recent.removeAll() }

    private func handle(_ event: CGEvent) {
        guard enabled, !suspended else { return }

        var length = 0
        var chars = [UniChar](repeating: 0, count: 4)
        event.keyboardGetUnicodeString(
            maxStringLength: 4, actualStringLength: &length, unicodeString: &chars
        )
        guard length == 1, let scalar = Unicode.Scalar(chars[0]) else {
            recent.removeAll(); return
        }
        let ch = Character(scalar)
        // Caracteres de control (Enter, Tab, Backspace, Esc): cortan la secuencia.
        if let a = ch.asciiValue, a < 32 { recent.removeAll(); return }

        recent.append(ch)
        if recent.count > 3 { recent.removeFirst(recent.count - 3) }

        if recent.count >= 2,
           recent[recent.count - 1] == "/", recent[recent.count - 2] == "/" {
            let preceding: Character? = recent.count >= 3 ? recent[recent.count - 3] : nil
            // No disparar dentro de URLs ("http://") ni en "///".
            if preceding == ":" || preceding == "/" { return }
            recent.removeAll()
            MainActor.assumeIsolated { self.onTrigger() }
        }
    }
}
