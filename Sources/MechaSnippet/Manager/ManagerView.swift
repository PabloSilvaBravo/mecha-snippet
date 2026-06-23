import SwiftUI
import MechaSnippetCore

struct ManagerView: View {
    @ObservedObject var store: SnippetStore
    @State private var selectedID: UUID?
    @State private var search = ""

    private var filtered: [Snippet] {
        search.isEmpty ? store.snippets : Matcher.filter(store.snippets, query: search)
    }
    private var selected: Snippet? { store.snippets.first { $0.id == selectedID } }

    var body: some View {
        NavigationSplitView {
            VStack(spacing: 0) {
                HStack(spacing: 8) {
                    TextField("Buscar…", text: $search)
                        .textFieldStyle(.roundedBorder)
                    Button { addNew() } label: { Image(systemName: "plus") }
                        .help("Nuevo snippet")
                }
                .padding(8)

                List(selection: $selectedID) {
                    ForEach(filtered) { s in
                        VStack(alignment: .leading, spacing: 2) {
                            Text(s.name).fontWeight(.medium).lineLimit(1)
                            Text(oneLine(s.content)).font(.caption)
                                .foregroundStyle(.secondary).lineLimit(1)
                        }
                        .tag(s.id)
                    }
                    .onMove { from, to in
                        // Reordenar solo cuando no hay búsqueda (los offsets de la
                        // lista filtrada no mapean al store).
                        guard search.isEmpty else { return }
                        store.move(fromOffsets: from, toOffset: to)
                    }
                }
                if !search.isEmpty {
                    Text("Reordenar disponible sin búsqueda")
                        .font(.caption2).foregroundStyle(.tertiary).padding(.bottom, 4)
                }
            }
            .frame(minWidth: 240)
        } detail: {
            if let sel = selected {
                EditorPane(store: store, snippet: sel).id(sel.id)
            } else {
                ContentUnavailableView(
                    "Elige o crea un snippet",
                    systemImage: "scissors",
                    description: Text("Usa el botón + para agregar uno nuevo.")
                )
            }
        }
        .frame(minWidth: 720, minHeight: 460)
        .navigationTitle("Mecha Snippet · \(store.snippets.count) snippets")
        .onAppear { if selectedID == nil { selectedID = store.snippets.first?.id } }
    }

    private func oneLine(_ s: String) -> String {
        s.replacingOccurrences(of: "\n", with: " ")
            .trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func addNew() {
        let s = Snippet(name: "nuevo", content: "")
        store.add(s)
        selectedID = s.id
        search = ""
    }
}

private struct EditorPane: View {
    @ObservedObject var store: SnippetStore
    let snippet: Snippet
    @State private var name = ""
    @State private var content = ""

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            TextField("Nombre", text: $name)
                .textFieldStyle(.roundedBorder)
                .font(.title3)

            TextEditor(text: $content)
                .font(.system(size: 13))
                .frame(minHeight: 240)
                .overlay(RoundedRectangle(cornerRadius: 6).stroke(.quaternary))

            HStack {
                Button {
                    store.add(Snippet(name: name + " copia", content: content))
                } label: { Label("Duplicar", systemImage: "doc.on.doc") }

                Spacer()

                Button(role: .destructive) {
                    store.delete(id: snippet.id)
                } label: { Label("Borrar", systemImage: "trash") }

                Button {
                    store.update(Snippet(id: snippet.id, name: name, content: content))
                } label: { Label("Guardar", systemImage: "checkmark") }
                    .keyboardShortcut("s")
                    .buttonStyle(.borderedProminent)
            }
        }
        .padding(16)
        .onAppear { name = snippet.name; content = snippet.content }
    }
}
