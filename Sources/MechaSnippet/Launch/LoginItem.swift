import ServiceManagement

/// Auto-arranque vía SMAppService usando un LaunchAgent embebido en el bundle
/// (Contents/Library/LaunchAgents/). El agente trae RunAtLoad + KeepAlive
/// {SuccessfulExit:false}: arranca al iniciar sesión y revive si se cae con
/// error, pero respeta el "Salir" limpio.
enum LoginItem {
    static let plistName = "io.github.pablosilvabravo.mechasnippet.plist"

    private static var service: SMAppService {
        SMAppService.agent(plistName: plistName)
    }

    static var isEnabled: Bool { service.status == .enabled }

    @discardableResult
    static func enable() -> Bool {
        do { try service.register(); return true }
        catch { NSLog("[mecha] no se pudo registrar el Login Item: \(error)"); return false }
    }

    @discardableResult
    static func disable() -> Bool {
        do { try service.unregister(); return true }
        catch { NSLog("[mecha] no se pudo quitar el Login Item: \(error)"); return false }
    }

    /// Diagnóstico para verificación: registra, lee el estado y desregistra.
    static func diagnose() -> String {
        var log = "status inicial: \(describe(service.status))\n"
        do { try service.register(); log += "register: OK\n" }
        catch { log += "register: ERROR \(error)\n" }
        log += "status tras register: \(describe(service.status))\n"
        do { try service.unregister(); log += "unregister: OK\n" }
        catch { log += "unregister: ERROR \(error)\n" }
        log += "status final: \(describe(service.status))\n"
        return log
    }

    private static func describe(_ s: SMAppService.Status) -> String {
        switch s {
        case .notRegistered: return "notRegistered"
        case .enabled: return "enabled"
        case .requiresApproval: return "requiresApproval"
        case .notFound: return "notFound"
        @unknown default: return "unknown(\(s.rawValue))"
        }
    }
}
