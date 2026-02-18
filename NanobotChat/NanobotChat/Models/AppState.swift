import Observation

@MainActor
@Observable
final class AppState {
    enum Tab: String, CaseIterable {
        case chat, canvas, files, logs
    }

    var selectedTab: Tab = .chat
    var showConnection = false
    var showSettings = false
    var showBotProfile = false
    var pendingFilePath: String? = nil
}
