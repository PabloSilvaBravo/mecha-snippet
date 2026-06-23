import Foundation

public struct Snippet: Identifiable, Codable, Equatable, Sendable {
    public var id: UUID
    public var name: String
    public var content: String

    public init(id: UUID = UUID(), name: String, content: String) {
        self.id = id
        self.name = name
        self.content = content
    }
}
