import AppKit
import CoreGraphics
import ApplicationServices

/// Pega un snippet en la app activa: borra el disparador, escribe el snippet en
/// el portapapeles (marcado como efímero), envía Cmd+V y restaura el
/// portapapeles original. Sin Accesibilidad no hace nada (para no comer texto).
enum Inserter {
    private static let keyDelete: CGKeyCode = 51
    private static let keyV: CGKeyCode = 9
    private static let concealed = "org.nspasteboard.ConcealedType"
    private static let transient = "org.nspasteboard.TransientType"
    private static let restoreDelay = 0.5

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

        DispatchQueue.main.asyncAfter(deadline: .now() + restoreDelay) {
            restore(pb, saved, expected: ourChange)
        }
    }

    private static func postKey(_ code: CGKeyCode, flags: CGEventFlags = []) {
        let src = CGEventSource(stateID: .hidSystemState)
        let down = CGEvent(keyboardEventSource: src, virtualKey: code, keyDown: true)
        let up = CGEvent(keyboardEventSource: src, virtualKey: code, keyDown: false)
        down?.flags = flags
        up?.flags = flags
        down?.post(tap: .cghidEventTap)
        up?.post(tap: .cghidEventTap)
    }

    private static func snapshot(_ pb: NSPasteboard) -> [[NSPasteboard.PasteboardType: Data]] {
        (pb.pasteboardItems ?? []).map { item in
            var d: [NSPasteboard.PasteboardType: Data] = [:]
            for t in item.types { if let data = item.data(forType: t) { d[t] = data } }
            return d
        }
    }

    private static func restore(
        _ pb: NSPasteboard,
        _ snap: [[NSPasteboard.PasteboardType: Data]],
        expected: Int
    ) {
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
