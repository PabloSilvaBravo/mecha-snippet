import Foundation

enum Paths {
    static let appDirName = "MechaSnippet"

    static var appSupportDir: URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        let dir = base.appendingPathComponent(appDirName, isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    static var snippetsURL: URL {
        appSupportDir.appendingPathComponent("snippets.json")
    }

    /// Copia el ejemplo embebido la primera vez. El JSON vive en
    /// Contents/Resources/ del bundle (lo copia el script de empaquetado),
    /// así que se lee con Bundle.main, sin resource bundles anidados.
    static func seedIfNeeded() {
        let dest = snippetsURL
        guard !FileManager.default.fileExists(atPath: dest.path) else { return }
        if let example = Bundle.main.url(forResource: "snippets.example", withExtension: "json") {
            try? FileManager.default.copyItem(at: example, to: dest)
        } else {
            try? Data("[]".utf8).write(to: dest)
        }
    }
}
