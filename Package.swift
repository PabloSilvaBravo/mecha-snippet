// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "MechaSnippet",
    platforms: [.macOS(.v26)],
    targets: [
        .target(name: "MechaSnippetCore"),
        .executableTarget(
            name: "MechaSnippet",
            dependencies: ["MechaSnippetCore"],
            resources: [.process("Resources")]
        ),
        .testTarget(
            name: "MechaSnippetCoreTests",
            dependencies: ["MechaSnippetCore"]
        ),
    ]
)
