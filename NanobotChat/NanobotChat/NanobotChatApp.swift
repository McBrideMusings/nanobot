import SwiftUI
#if os(macOS)
import AppKit
#endif

@main
struct NanobotChatApp: App {
    @State private var client = WebSocketClient()

    init() {
        #if os(macOS)
        NSApplication.shared.setActivationPolicy(.regular)
        NSApplication.shared.activate(ignoringOtherApps: true)
        #endif
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(client)
        }
    }
}
