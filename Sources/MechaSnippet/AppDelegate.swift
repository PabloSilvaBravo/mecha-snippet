import AppKit

/// Permite disparar vistas al arrancar mediante variables de entorno, para poder
/// capturar la interfaz de forma automatizada en la verificación visual.
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
        if env["MECHA_DEBUG_ONBOARDING"] == "1" { after(0.8) { state.showOnboarding() } }
    }
}
