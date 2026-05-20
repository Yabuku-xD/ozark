// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "OzarkRunner",
    platforms: [
        .macOS(.v13)
    ],
    targets: [
        .executableTarget(
            name: "OzarkRunner",
            path: "Sources/OzarkRunner"
        )
    ]
)
