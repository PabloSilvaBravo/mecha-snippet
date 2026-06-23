import SwiftUI
import MechaSnippetCore

struct QuickAddView: View {
    @ObservedObject var store: SnippetStore
    var onDismiss: () -> Void

    @State private var name = ""
    @State private var content = ""

    private var canSave: Bool {
        !name.trimmingCharacters(in: .whitespaces).isEmpty
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Nuevo snippet").font(.headline)

            TextField("Nombre", text: $name)
                .textFieldStyle(.roundedBorder)

            TextEditor(text: $content)
                .font(.system(size: 13))
                .frame(height: 140)
                .overlay(RoundedRectangle(cornerRadius: 6).stroke(.quaternary))

            HStack {
                Spacer()
                Button("Cancelar") { onDismiss() }
                Button("Guardar") {
                    let n = name.trimmingCharacters(in: .whitespaces)
                    if !n.isEmpty { store.add(Snippet(name: n, content: content)) }
                    onDismiss()
                }
                .keyboardShortcut(.return)
                .disabled(!canSave)
                .buttonStyle(.borderedProminent)
            }
        }
        .padding(16)
        .frame(width: 380)
    }
}
