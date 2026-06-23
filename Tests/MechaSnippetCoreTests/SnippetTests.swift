import Testing
import Foundation
@testable import MechaSnippetCore

@Test func snippetTieneIdUnicoPorDefecto() {
    let a = Snippet(name: "x", content: "y")
    let b = Snippet(name: "x", content: "y")
    #expect(a.id != b.id)
}

@Test func snippetCodableRoundTrip() throws {
    let s = Snippet(name: "saludo", content: "Hola\ncómo estás")
    let data = try JSONEncoder().encode(s)
    let back = try JSONDecoder().decode(Snippet.self, from: data)
    #expect(back.name == s.name)
    #expect(back.content == s.content)
}
