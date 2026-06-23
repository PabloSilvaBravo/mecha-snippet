import SwiftUI

struct OnboardingView: View {
    @State private var ax = Permissions.accessibility
    @State private var input = Permissions.inputMonitoring
    private let timer = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    private var allGranted: Bool { ax && input }

    var body: some View {
        VStack(alignment: .leading, spacing: 18) {
            VStack(alignment: .leading, spacing: 6) {
                Text("Bienvenido a Mecha Snippet").font(.title2).bold()
                Text("Escribe // en cualquier app y pega tus textos al instante. Para eso, macOS pide dos permisos.")
                    .foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }

            permissionRow(
                ok: input,
                titulo: "Monitoreo de entrada",
                desc: "Para detectar cuando escribes //"
            ) {
                Permissions.requestInputMonitoring()
                Permissions.openInputMonitoringSettings()
            }

            permissionRow(
                ok: ax,
                titulo: "Accesibilidad",
                desc: "Para pegar el snippet con Cmd+V"
            ) {
                Permissions.promptAccessibility()
                Permissions.openAccessibilitySettings()
            }

            Divider()

            if allGranted {
                Label("¡Listo! Escribe // en cualquier app para empezar.", systemImage: "checkmark.seal.fill")
                    .foregroundStyle(.green).font(.headline)
            } else {
                Text("Tras conceder cada permiso, esta ventana se actualiza sola. Si no, reabre la app.")
                    .font(.caption).foregroundStyle(.tertiary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .padding(28)
        .frame(width: 480)
        .onReceive(timer) { _ in
            ax = Permissions.accessibility
            input = Permissions.inputMonitoring
        }
    }

    private func permissionRow(
        ok: Bool, titulo: String, desc: String, action: @escaping () -> Void
    ) -> some View {
        HStack(spacing: 12) {
            Image(systemName: ok ? "checkmark.circle.fill" : "circle")
                .foregroundStyle(ok ? .green : .secondary)
                .font(.title2)
            VStack(alignment: .leading, spacing: 2) {
                Text(titulo).fontWeight(.semibold)
                Text(desc).font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            if ok {
                Text("Concedido").font(.caption).foregroundStyle(.green)
            } else {
                Button("Conceder", action: action).buttonStyle(.borderedProminent)
            }
        }
    }
}
