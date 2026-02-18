import SwiftUI

struct ConnectionView: View {
    @Environment(WebSocketClient.self) private var client
    @Environment(\.dismiss) private var dismiss
    @AppStorage("serverURL") private var savedURL = "ws://100.114.249.118:18790"
    @State private var editingURL = ""
    @State private var isTesting = false
    @State private var testResult: StatusResult? = nil
    @State private var testFailed = false

    var body: some View {
        NavigationStack {
            Form {
                Section("Server URL") {
                    TextField("ws://host:port", text: $editingURL)
                        #if os(iOS)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                        #endif
                        .autocorrectionDisabled()

                    Button("Save & Reconnect") {
                        savedURL = editingURL
                        client.disconnect()
                        client.connect()
                        dismiss()
                    }
                }

                Section("Test Connection") {
                    if isTesting {
                        HStack {
                            ProgressView()
                            Text("Testing...")
                                .foregroundStyle(.secondary)
                        }
                    } else {
                        Button("Test Connection") {
                            Task { await runTest() }
                        }
                    }

                    if testFailed && !isTesting {
                        Label("Connection failed", systemImage: "xmark.circle")
                            .foregroundStyle(.red)
                    }

                    if let result = testResult {
                        LabeledContent("Latency", value: String(format: "%.0f ms", result.latencyMs))
                        LabeledContent("Model", value: result.model.isEmpty ? "—" : result.model)
                        LabeledContent("Uptime", value: formattedUptime(result.uptimeSeconds))
                    }
                }

                if let result = testResult {
                    Section("System") {
                        LabeledContent("Host", value: result.host.isEmpty ? "—" : result.host)
                        LabeledContent("Backend", value: result.backend.isEmpty ? "—" : result.backend)
                        LabeledContent("Gateway", value: result.gatewayURL.isEmpty ? "—" : result.gatewayURL)
                    }

                    if !result.capabilities.isEmpty {
                        Section("Capabilities") {
                            LazyVGrid(columns: [GridItem(.adaptive(minimum: 80))], alignment: .leading, spacing: 8) {
                                ForEach(result.capabilities, id: \.self) { cap in
                                    Text(cap)
                                        .font(.caption)
                                        .padding(.horizontal, 10)
                                        .padding(.vertical, 4)
                                        .background(Color.accentColor.opacity(0.15))
                                        .foregroundStyle(Color.accentColor)
                                        .clipShape(Capsule())
                                }
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
            }
            .navigationTitle("Connection")
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

    private func runTest() async {
        isTesting = true
        testResult = nil
        testFailed = false
        let (_, result) = await client.testConnection(url: editingURL)
        isTesting = false
        if let result {
            testResult = result
        } else {
            testFailed = true
        }
    }

    private func formattedUptime(_ seconds: Double) -> String {
        let total = Int(seconds)
        let h = total / 3600
        let m = (total % 3600) / 60
        let s = total % 60
        if h > 0 { return "\(h)h \(m)m \(s)s" }
        if m > 0 { return "\(m)m \(s)s" }
        return "\(s)s"
    }
}
