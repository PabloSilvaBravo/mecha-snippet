import SwiftUI
import MechaSnippetCore

/// Estado del panel rápido, compartido entre la vista SwiftUI y el NSPanel
/// (que maneja el teclado con un monitor de eventos, más confiable que
/// .onKeyPress dentro de un panel no-activante).
@MainActor
final class PanelModel: ObservableObject {
    @Published var query = ""
    @Published var selection = 0
    let store: SnippetStore
    var onInsert: (Snippet) -> Void = { _ in }
    var onClose: () -> Void = {}

    init(store: SnippetStore) { self.store = store }

    var results: [Snippet] { Matcher.filter(store.snippets, query: query) }

    func resetForShow() { query = ""; selection = 0 }

    func move(_ delta: Int) {
        let r = results
        guard !r.isEmpty else { return }
        selection = max(0, min(r.count - 1, selection + delta))
    }

    func insertCurrent() {
        let r = results
        guard r.indices.contains(selection) else { return }
        onInsert(r[selection])
    }
}

struct SearchPanelView: View {
    @ObservedObject var model: PanelModel
    @FocusState private var searchFocused: Bool

    var body: some View {
        let results = model.results
        VStack(spacing: 10) {
            HStack(spacing: 8) {
                Image(systemName: "magnifyingglass").foregroundStyle(.secondary)
                TextField("Buscar snippet…", text: $model.query)
                    .textFieldStyle(.plain)
                    .font(.system(size: 16))
                    .focused($searchFocused)
                    .onChange(of: model.query) { model.selection = 0 }
                    .onSubmit { model.insertCurrent() }
            }

            if results.isEmpty {
                emptyState
            } else {
                HStack(alignment: .top, spacing: 12) {
                    listColumn(results)
                    previewColumn(results)
                }
            }

            shortcutsBar
        }
        .padding(16)
        .frame(width: 600)
        .glassBackground(cornerRadius: 20)
        .onAppear { searchFocused = true }
    }

    private var emptyState: some View {
        VStack(spacing: 6) {
            Image(systemName: "tray").font(.largeTitle).foregroundStyle(.tertiary)
            Text("Sin resultados").foregroundStyle(.secondary)
        }
        .frame(width: 552, height: 200)
    }

    private var shortcutsBar: some View {
        HStack(spacing: 14) {
            keyHint("↑↓", "navegar")
            keyHint("↵", "pegar")
            keyHint("esc", "cerrar")
            Spacer()
        }
        .font(.caption2)
        .foregroundStyle(.tertiary)
    }

    private func keyHint(_ key: String, _ label: String) -> some View {
        HStack(spacing: 4) {
            Text(key).padding(.horizontal, 5).padding(.vertical, 1)
                .background(.secondary.opacity(0.18), in: RoundedRectangle(cornerRadius: 4))
            Text(label)
        }
    }

    @ViewBuilder
    private func listColumn(_ results: [Snippet]) -> some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 2) {
                    ForEach(Array(results.enumerated()), id: \.element.id) { i, s in
                        HStack {
                            Text(s.name).lineLimit(1).font(.system(size: 13, weight: .medium))
                            Spacer(minLength: 0)
                        }
                        .padding(.horizontal, 8)
                        .padding(.vertical, 6)
                        .background(
                            i == model.selection ? Color.accentColor.opacity(0.25) : Color.clear,
                            in: RoundedRectangle(cornerRadius: 6)
                        )
                        .contentShape(Rectangle())
                        .onTapGesture { model.selection = i; model.insertCurrent() }
                        .id(i)
                    }
                }
                .padding(.vertical, 2)
            }
            .frame(width: 220, height: 280)
            .onChange(of: model.selection) { proxy.scrollTo(model.selection, anchor: .center) }
        }
    }

    @ViewBuilder
    private func previewColumn(_ results: [Snippet]) -> some View {
        let current = results.indices.contains(model.selection) ? results[model.selection] : nil
        VStack(alignment: .leading, spacing: 6) {
            if let current {
                Text(current.name)
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                Divider()
            }
            ScrollView {
                Text(current?.content ?? "")
                    .font(.system(size: 13))
                    .lineSpacing(2)
                    .frame(maxWidth: .infinity, alignment: .topLeading)
                    .textSelection(.enabled)
            }
        }
        .frame(width: 320, height: 280)
        .padding(10)
        .background(.black.opacity(0.05), in: RoundedRectangle(cornerRadius: 10))
    }
}
