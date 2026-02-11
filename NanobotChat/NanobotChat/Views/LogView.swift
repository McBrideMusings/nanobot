import SwiftUI

struct LogView: View {
    @Environment(WebSocketClient.self) private var client
    @Environment(\.dismiss) private var dismiss
    @State private var copied = false

    private var allLogsText: String {
        client.logEntries.map(\.formatted).joined(separator: "\n")
    }

    var body: some View {
        NavigationStack {
            Group {
                if client.logEntries.isEmpty {
                    ContentUnavailableView(
                        "No Logs",
                        systemImage: "text.alignleft",
                        description: Text("Connect and send a message to see logs.")
                    )
                } else {
                    ScrollViewReader { proxy in
                        ScrollView {
                            Text(allLogsText)
                                .font(.system(.caption, design: .monospaced))
                                .foregroundStyle(.secondary)
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding()
                                .textSelection(.enabled)
                                .id("logBottom")
                        }
                        .onAppear {
                            proxy.scrollTo("logBottom", anchor: .bottom)
                        }
                        .onChange(of: client.logEntries.count) {
                            withAnimation {
                                proxy.scrollTo("logBottom", anchor: .bottom)
                            }
                        }
                    }
                }
            }
            .navigationTitle("Logs")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .automatic) {
                    Button {
                        #if os(iOS)
                        UIPasteboard.general.string = allLogsText
                        #else
                        NSPasteboard.general.clearContents()
                        NSPasteboard.general.setString(allLogsText, forType: .string)
                        #endif
                        copied = true
                        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                            copied = false
                        }
                    } label: {
                        Label(copied ? "Copied!" : "Copy All", systemImage: copied ? "checkmark" : "doc.on.doc")
                    }
                    .disabled(client.logEntries.isEmpty)
                }
                ToolbarItem(placement: .automatic) {
                    Button {
                        client.clearLogs()
                    } label: {
                        Label("Clear", systemImage: "trash")
                    }
                    .disabled(client.logEntries.isEmpty)
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}
