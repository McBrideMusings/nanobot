import SwiftUI

struct FileEditorView: View {
    let path: String
    @Environment(WebSocketClient.self) private var client
    @Environment(\.dismiss) private var dismiss
    @State private var editedContent = ""
    @State private var isDirty = false
    @State private var initialLoadDone = false

    private var filename: String {
        URL(fileURLWithPath: path).lastPathComponent
    }

    var body: some View {
        TextEditor(text: $editedContent)
            .font(.system(.body, design: .monospaced))
            .onChange(of: editedContent) { _, _ in
                if initialLoadDone { isDirty = true }
            }
            .navigationTitle(filename + (isDirty ? " •" : ""))
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        client.writeFile(path: path, content: editedContent)
                        isDirty = false
                    }
                    .disabled(!isDirty)
                }
                if isDirty {
                    ToolbarItem(placement: .cancellationAction) {
                        Button("Cancel") {
                            // Reload from cache
                            if let cached = client.workspaceFileContent, cached.path == path {
                                editedContent = cached.content
                            }
                            isDirty = false
                        }
                    }
                }
            }
            .safeAreaInset(edge: .bottom) {
                saveStatusBanner
            }
            .onAppear {
                if let cached = client.workspaceFileContent, cached.path == path {
                    editedContent = cached.content
                    initialLoadDone = true
                } else {
                    client.readFile(path: path)
                }
            }
            .onChange(of: client.workspaceFileContent?.path) { _, newPath in
                guard !initialLoadDone, newPath == path,
                      let content = client.workspaceFileContent else { return }
                editedContent = content.content
                initialLoadDone = true
                isDirty = false
            }
    }

    @ViewBuilder
    private var saveStatusBanner: some View {
        switch client.workspaceSaveStatus {
        case .saving:
            statusBanner("Saving...", systemImage: "arrow.up.circle", color: .secondary)
        case .saved:
            statusBanner("Saved", systemImage: "checkmark.circle.fill", color: .green)
        case .error:
            statusBanner("Save failed", systemImage: "xmark.circle.fill", color: .red)
        case .idle:
            EmptyView()
        }
    }

    private func statusBanner(_ text: String, systemImage: String, color: Color) -> some View {
        Label(text, systemImage: systemImage)
            .font(.caption)
            .foregroundStyle(color)
            .padding(.vertical, 6)
            .padding(.horizontal, 14)
            .background(.bar)
            .clipShape(Capsule())
            .padding(.bottom, 8)
    }
}
