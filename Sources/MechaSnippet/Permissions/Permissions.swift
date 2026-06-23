import AppKit
import ApplicationServices
import IOKit.hid

/// Chequeo y solicitud de los dos permisos que necesita Mecha Snippet:
/// Accesibilidad (para enviar Cmd+V) y Monitoreo de entrada (para escuchar "//").
enum Permissions {
    static var accessibility: Bool { AXIsProcessTrusted() }

    static var inputMonitoring: Bool {
        IOHIDCheckAccess(kIOHIDRequestTypeListenEvent) == kIOHIDAccessTypeGranted
    }

    /// Muestra el diálogo del sistema que agrega la app a la lista de Accesibilidad.
    static func promptAccessibility() {
        // Valor de kAXTrustedCheckOptionPrompt (usar el literal evita el acceso a
        // una global de C que Swift 6 marca como no concurrency-safe).
        let key = "AXTrustedCheckOptionPrompt"
        _ = AXIsProcessTrustedWithOptions([key: true] as CFDictionary)
    }

    /// Solicita Monitoreo de entrada (abre el diálogo del sistema la primera vez).
    static func requestInputMonitoring() {
        _ = IOHIDRequestAccess(kIOHIDRequestTypeListenEvent)
    }

    static func openAccessibilitySettings() {
        open("x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")
    }

    static func openInputMonitoringSettings() {
        open("x-apple.systempreferences:com.apple.preference.security?Privacy_ListenEvent")
    }

    private static func open(_ s: String) {
        if let url = URL(string: s) { NSWorkspace.shared.open(url) }
    }
}
