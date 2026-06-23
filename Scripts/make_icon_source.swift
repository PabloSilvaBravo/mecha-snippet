import AppKit

// Genera el icon-source.png (1024x1024): tijera blanca sobre un squircle con
// gradiente. Uso: swift Scripts/make_icon_source.swift

let size: CGFloat = 1024
let rep = NSBitmapImageRep(
    bitmapDataPlanes: nil, pixelsWide: Int(size), pixelsHigh: Int(size),
    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
    colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0
)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)

let rect = NSRect(x: 0, y: 0, width: size, height: size)
let corner = size * 0.2237
let path = NSBezierPath(roundedRect: rect, xRadius: corner, yRadius: corner)
path.addClip()

let gradient = NSGradient(
    starting: NSColor(red: 0.30, green: 0.40, blue: 0.95, alpha: 1.0),
    ending: NSColor(red: 0.16, green: 0.20, blue: 0.55, alpha: 1.0)
)!
gradient.draw(in: rect, angle: -90)

let config = NSImage.SymbolConfiguration(paletteColors: [.white])
    .applying(NSImage.SymbolConfiguration(pointSize: size * 0.46, weight: .medium))
if let sym = NSImage(systemSymbolName: "scissors", accessibilityDescription: nil)?
    .withSymbolConfiguration(config) {
    let ss = sym.size
    let origin = NSPoint(x: (size - ss.width) / 2, y: (size - ss.height) / 2)
    sym.draw(at: origin, from: .zero, operation: .sourceOver, fraction: 1.0)
}

NSGraphicsContext.restoreGraphicsState()

let out = URL(fileURLWithPath: "Resources/icon-source.png")
try? FileManager.default.createDirectory(
    at: out.deletingLastPathComponent(), withIntermediateDirectories: true
)
if let data = rep.representation(using: .png, properties: [:]) {
    try! data.write(to: out)
    print("==> \(out.path) generado (\(Int(size))x\(Int(size)))")
}
