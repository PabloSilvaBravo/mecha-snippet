import Foundation

enum Prefs {
    private static let originKey = "panelOriginV2"

    static var panelOrigin: CGPoint? {
        get {
            guard let d = UserDefaults.standard.dictionary(forKey: originKey),
                  let x = d["x"] as? Double, let y = d["y"] as? Double else { return nil }
            return CGPoint(x: x, y: y)
        }
        set {
            if let p = newValue {
                UserDefaults.standard.set(["x": p.x, "y": p.y], forKey: originKey)
            } else {
                UserDefaults.standard.removeObject(forKey: originKey)
            }
        }
    }
}
