import SwiftUI
#if os(macOS)
import AppKit
#endif

@main
struct NanobotChatApp: App {
    @State private var client = WebSocketClient()
    @State private var appState = AppState()

    init() {
        #if os(macOS)
        NSApplication.shared.setActivationPolicy(.regular)
        NSApplication.shared.activate(ignoringOtherApps: true)
        #endif
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(client)
                .environment(appState)
        }
    }
}
