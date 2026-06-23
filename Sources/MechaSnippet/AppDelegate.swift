import AppKit

/// Disparadores opcionales por variable de entorno para verificación visual.
/// Ej: MECHA_DEBUG_PANEL=1 open "Mecha Snippet.app"
final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        let env = ProcessInfo.processInfo.environment
        let state = AppState.shared

        func after(_ seconds: Double, _ action: @escaping @MainActor () -> Void) {
            Task { @MainActor in
                try? await Task.sleep(for: .seconds(seconds))
                action()
            }
        }

        if env["MECHA_DEBUG_PANEL"] == "1" { after(0.8) { state.showPanel() } }
        if env["MECHA_DEBUG_MANAGER"] == "1" { after(0.8) { state.showManager() } }
        if env["MECHA_DEBUG_QUICKADD"] == "1" { after(0.8) { state.showQuickAdd() } }

        // Primera corrida: si faltan permisos, guiar al usuario y disparar los
        // diálogos del sistema (la app aparece en Ajustes para activar el toggle).
        if env["MECHA_NO_ONBOARDING"] != "1", state.needsPermissions {
            after(0.6) {
                state.showOnboarding()
                state.requestPermissions()
            }
        }
    }
}
