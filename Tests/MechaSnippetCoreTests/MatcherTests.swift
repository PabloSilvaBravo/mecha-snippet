import Testing
@testable import MechaSnippetCore

private let data = [
    Snippet(name: "saludo", content: "Hola cómo estás"),
    Snippet(name: "pago", content: "datos de transferencia"),
    Snippet(name: "México", content: "envío internacional"),
]

@Test func sinQueryDevuelveTodo() {
    #expect(Matcher.filter(data, query: "").count == 3)
}

@Test func ignoraTildes() {
    #expect(Matcher.filter(data, query: "mexico").map(\.name) == ["México"])
}

@Test func multipalabraExigeTodas() {
    #expect(Matcher.filter(data, query: "datos transferencia").map(\.name) == ["pago"])
    #expect(Matcher.filter(data, query: "datos zzz").isEmpty)
}

@Test func rankingPrefijoNombrePrimero() {
    let items = [
        Snippet(name: "saludo formal", content: "x"),
        Snippet(name: "formal", content: "y"),
    ]
    // "formal" empieza con la query -> va primero
    #expect(Matcher.filter(items, query: "formal").map(\.name) == ["formal", "saludo formal"])
}
