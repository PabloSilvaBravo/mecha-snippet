import Testing
import Foundation
@testable import MechaSnippetCore

private func tmpURL() -> URL {
    FileManager.default.temporaryDirectory
        .appendingPathComponent("mecha-\(UUID().uuidString).json")
}

@Test func leeFormatoDictLegacy() {
    let json = #"{"saludo":"Hola","pago":"Datos"}"#.data(using: .utf8)!
    let items = SnippetStore.decode(json)!
    #expect(items.count == 2)
    #expect(items.contains { $0.name == "saludo" && $0.content == "Hola" })
}

@Test func leeFormatoListaNameContent() {
    let json = #"[{"name":"a","content":"1"},{"name":"b","content":"2"}]"#.data(using: .utf8)!
    let items = SnippetStore.decode(json)!
    #expect(items.map(\.name) == ["a", "b"])  // preserva orden
}

@Test func jsonCorruptoDevuelveNil() {
    #expect(SnippetStore.decode(Data("{no es json".utf8)) == nil)
}

@Test func reparaComillasTipograficas() {
    // JSON con comillas dobles tipográficas (lo que deja TextEdit con
    // sustituciones activadas). Debe repararse y parsear igual.
    let json = "{\u{201C}saludo\u{201D}:\u{201C}Hola\u{201D}}".data(using: .utf8)!
    let items = SnippetStore.decode(json)!
    #expect(items.count == 1)
    #expect(items.first?.name == "saludo")
    #expect(items.first?.content == "Hola")
}

@Test func guardadoYReloadRoundTrip() throws {
    let url = tmpURL()
    defer { try? FileManager.default.removeItem(at: url) }
    let store = SnippetStore(fileURL: url)
    store.add(Snippet(name: "x", content: "y"))
    let store2 = SnippetStore(fileURL: url)
    store2.load()
    #expect(store2.snippets.map(\.name) == ["x"])
}

@Test func reloadCorruptoConservaMemoria() throws {
    let url = tmpURL()
    defer { try? FileManager.default.removeItem(at: url) }
    let store = SnippetStore(fileURL: url)
    store.add(Snippet(name: "bueno", content: "1"))
    try Data("{roto".utf8).write(to: url)
    store.load()
    #expect(store.snippets.map(\.name) == ["bueno"])  // no se borró
}

@Test func moveReordena() {
    let url = tmpURL()
    defer { try? FileManager.default.removeItem(at: url) }
    let store = SnippetStore(fileURL: url)
    store.add(Snippet(name: "a", content: "1"))
    store.add(Snippet(name: "b", content: "2"))
    store.move(fromOffsets: IndexSet(integer: 1), toOffset: 0)
    #expect(store.snippets.map(\.name) == ["b", "a"])
}
