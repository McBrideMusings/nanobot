import SwiftUI

struct FilesTabView: View {
    @Environment(WebSocketClient.self) private var client
    @Environment(AppState.self) private var appState
    @State private var navPath = NavigationPath()

    var body: some View {
        @Bindable var appState = appState
        NavigationStack(path: $navPath) {
            FileDirectoryView(path: "")
                .navigationDestination(for: String.self) { path in
                    if isDirectory(path) {
                        FileDirectoryView(path: path)
                    } else {
                        FileEditorView(path: path)
                    }
                }
        }
        .onChange(of: appState.pendingFilePath) { _, pending in
            guard let path = pending else { return }
            navPath.removeLast(navPath.count)
            navPath.append(path)
            appState.pendingFilePath = nil
        }
    }

    private func isDirectory(_ path: String) -> Bool {
        // Check cache first: look for an entry in the parent directory
        let url = URL(fileURLWithPath: "/" + path)
        let parentPath = url.deletingLastPathComponent().relativePath
            .trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        let name = url.lastPathComponent
        let key = parentPath.isEmpty ? "." : parentPath
        if let entries = client.workspaceEntries[key],
           let entry = entries.first(where: { $0.name == name }) {
            return entry.is_dir
        }
        // Also check root "."
        if let entries = client.workspaceEntries["."],
           let entry = entries.first(where: { $0.name == name }) {
            return entry.is_dir
        }
        return false
    }
}
