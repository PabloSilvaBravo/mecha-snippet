import Foundation

public struct Matcher {
    public static func normalize(_ text: String) -> String {
        text.folding(options: [.diacriticInsensitive, .caseInsensitive], locale: nil)
    }

    public static func filter(
        _ snippets: [Snippet],
        query: String,
        normalizedCache: [UUID: (name: String, content: String)]? = nil
    ) -> [Snippet] {
        let q = normalize(query).trimmingCharacters(in: .whitespaces)
        if q.isEmpty { return snippets }
        let tokens = q.split(separator: " ").map(String.init)

        var scored: [(score: Int, name: String, snippet: Snippet)] = []
        for s in snippets {
            let normName = normalizedCache?[s.id]?.name ?? normalize(s.name)
            let normContent = normalizedCache?[s.id]?.content ?? normalize(s.content)
            let haystack = normName + "\n" + normContent
            guard tokens.allSatisfy({ haystack.contains($0) }) else { continue }

            let score: Int
            if normName.hasPrefix(q) { score = 0 }
            else if normName.contains(q) { score = 1 }
            else if tokens.allSatisfy({ normName.contains($0) }) { score = 2 }
            else { score = 3 }
            scored.append((score, normName, s))
        }
        scored.sort { $0.score != $1.score ? $0.score < $1.score : $0.name < $1.name }
        return scored.map(\.snippet)
    }
}
