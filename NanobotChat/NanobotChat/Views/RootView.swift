import SwiftUI

struct RootView: View {
    @Environment(WebSocketClient.self) private var client
    @Environment(AppState.self) private var appState
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        @Bindable var appState = appState
        VStack(spacing: 0) {
            AgentHeaderView()
            TabView(selection: $appState.selectedTab) {
                ChatTabView()
                    .tabItem {
                        Label("Chat", systemImage: "bubble.left.and.bubble.right")
                    }
                    .tag(AppState.Tab.chat)

                CanvasPlaceholderView()
                    .tabItem {
                        Label("Canvas", systemImage: "rectangle.on.rectangle")
                    }
                    .tag(AppState.Tab.canvas)

                FilesTabView()
                    .tabItem {
                        Label("Files", systemImage: "folder")
                    }
                    .tag(AppState.Tab.files)

                LogTabView()
                    .tabItem {
                        Label("Logs", systemImage: "terminal")
                    }
                    .tag(AppState.Tab.logs)
            }
        }
        .sheet(isPresented: $appState.showConnection) {
            ConnectionView()
        }
        .sheet(isPresented: $appState.showSettings) {
            SettingsView()
        }
        .sheet(isPresented: $appState.showBotProfile) {
            BotProfilePlaceholderView()
        }
        .onAppear {
            client.connect()
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .active && !client.isConnected {
                client.connect()
            }
        }
    }
}
