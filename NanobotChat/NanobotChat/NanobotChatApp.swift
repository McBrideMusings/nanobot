import SwiftUI

@main
struct NanobotChatApp: App {
    @State private var client = WebSocketClient()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(client)
        }
    }
}
