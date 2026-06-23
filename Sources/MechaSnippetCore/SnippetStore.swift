import Foundation

public final class SnippetStore: ObservableObject {
    @Published public private(set) var snippets: [Snippet] = []
    public let fileURL: URL

    public init(fileURL: URL) {
        self.fileURL = fileURL
        load()
    }

    public func load() {
        guard let data = try? Data(contentsOf: fileURL) else { return }
        if data.isEmpty { snippets = []; return }
        if let parsed = Self.decode(data) {
            snippets = parsed
        }
        // Si no parsea, se conserva lo que haya en memoria.
    }

    /// Parser puro de los tres formatos aceptados. nil si no es JSON válido.
    public static func decode(_ data: Data) -> [Snippet]? {
        guard let obj = try? JSONSerialization.jsonObject(with: data) else { return nil }
        if let dict = obj as? [String: Any] {
            // Formato 1.x: {"nombre":"contenido"} — orden no garantizado.
            return dict.map { Snippet(name: $0.key, content: String(describing: $0.value)) }
                .sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }
        }
        if let arr = obj as? [[String: Any]] {
            return arr.compactMap { entry in
                guard let name = (entry["name"] ?? entry["key"]) as? String, !name.isEmpty
                else { return nil }
                let content = (entry["content"] ?? entry["value"]) as? String ?? ""
                return Snippet(name: name, content: content)
            }
        }
        return nil
    }

    public func save() throws {
        let payload = snippets.map { ["name": $0.name, "content": $0.content] }
        let data = try JSONSerialization.data(
            withJSONObject: payload, options: [.prettyPrinted, .withoutEscapingSlashes]
        )
        try FileManager.default.createDirectory(
            at: fileURL.deletingLastPathComponent(), withIntermediateDirectories: true
        )
        let tmp = fileURL.deletingLastPathComponent()
            .appendingPathComponent(".\(UUID().uuidString).tmp")
        try data.write(to: tmp, options: .atomic)
        // rename atómico sobre el definitivo
        _ = try FileManager.default.replaceItemAt(fileURL, withItemAt: tmp)
        try? FileManager.default.setAttributes([.posixPermissions: 0o600], ofItemAtPath: fileURL.path)
    }

    private func persist() { try? save() }

    public func add(_ s: Snippet) { snippets.append(s); persist() }
    public func update(_ s: Snippet) {
        if let i = snippets.firstIndex(where: { $0.id == s.id }) { snippets[i] = s; persist() }
    }
    public func delete(id: UUID) { snippets.removeAll { $0.id == id }; persist() }
    /// Misma semántica que `Array.move(fromOffsets:toOffset:)` de SwiftUI (onMove),
    /// implementada sin depender de SwiftUI para que Core quede testeable.
    public func move(fromOffsets source: IndexSet, toOffset destination: Int) {
        let moving = source.map { snippets[$0] }
        var result = snippets
        for index in source.sorted(by: >) { result.remove(at: index) }
        let adjustedDest = destination - source.filter { $0 < destination }.count
        result.insert(contentsOf: moving, at: adjustedDest)
        snippets = result
        persist()
    }
}
