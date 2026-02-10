// swift-tools-version: 5.9
// This Package.swift provides structure for SPM-aware editors.
// The actual iOS/macOS build requires an Xcode project (.xcodeproj),
// which must be created on a Mac with Xcode 15+.

import PackageDescription

let package = Package(
    name: "NanobotChat",
    platforms: [
        .iOS(.v17),
        .macOS(.v14),
    ],
    targets: [
        .executableTarget(
            name: "NanobotChat",
            path: "NanobotChat"
        ),
    ]
)
