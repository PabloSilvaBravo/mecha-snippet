import SwiftUI

@main
struct MechaSnippetApp: App {
    var body: some Scene {
        MenuBarExtra("Mecha Snippet", systemImage: "scissors") {
            Text("Mecha Snippet 2.0")
            Divider()
            Button("Salir") { NSApplication.shared.terminate(nil) }
                .keyboardShortcut("q")
        }
        .menuBarExtraStyle(.menu)
    }
}
