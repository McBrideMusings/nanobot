import SwiftUI

struct SettingsView: View {
    @Environment(WebSocketClient.self) private var client
    @Environment(\.dismiss) private var dismiss
    @AppStorage("serverURL") private var savedURL = "ws://100.114.249.118:18790"
    @State private var editingURL = ""

    var body: some View {
        NavigationStack {
            Form {
                Section("Server") {
                    TextField("WebSocket URL", text: $editingURL)
                        #if os(iOS)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                        #endif
                        .autocorrectionDisabled()

                    HStack {
                        Circle()
                            .fill(client.isConnected ? .green : .red)
                            .frame(width: 8, height: 8)
                        Text(client.isConnected ? "Connected" : "Disconnected")
                            .foregroundStyle(.secondary)
                    }
                }

                Section {
                    Button("Reconnect") {
                        savedURL = editingURL
                        client.disconnect()
                        client.connect()
                    }
                }
            }
            .navigationTitle("Settings")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
            .onAppear { editingURL = savedURL }
        }
    }
}
