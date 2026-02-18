import SwiftUI

struct AgentHeaderView: View {
    @Environment(WebSocketClient.self) private var client
    @Environment(AppState.self) private var appState

    var body: some View {
        @Bindable var appState = appState
        HStack(spacing: 12) {
            // Avatar with status dot
            Button {
                appState.showBotProfile = true
            } label: {
                ZStack(alignment: .bottomTrailing) {
                    Circle()
                        .fill(Color.accentColor.opacity(0.15))
                        .frame(width: 36, height: 36)
                        .overlay {
                            Image(systemName: "cpu.fill")
                                .font(.system(size: 16))
                                .foregroundStyle(Color.accentColor)
                        }
                    Circle()
                        .fill(statusColor)
                        .frame(width: 10, height: 10)
                        .overlay {
                            Circle().stroke(statusDotBorderColor, lineWidth: 1.5)
                        }
                }
            }
            .buttonStyle(.plain)

            // Name + status
            VStack(alignment: .leading, spacing: 1) {
                Text("Nanobot")
                    .font(.headline)
                Text(statusText)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            // Connection button
            Button {
                appState.showConnection = true
            } label: {
                Image(systemName: "network")
                    .font(.system(size: 17))
            }
            .buttonStyle(.plain)
            .foregroundStyle(.secondary)

            // Settings button
            Button {
                appState.showSettings = true
            } label: {
                Image(systemName: "gearshape")
                    .font(.system(size: 17))
            }
            .buttonStyle(.plain)
            .foregroundStyle(.secondary)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
        .background(.bar)
    }

    private var statusDotBorderColor: Color {
        #if os(iOS)
        Color(UIColor.systemBackground)
        #else
        Color(NSColor.windowBackgroundColor)
        #endif
    }

    private var statusText: String {
        if client.isWaitingForResponse { return "Thinking..." }
        return client.isConnected ? "Online" : "Offline"
    }

    private var statusColor: Color {
        if client.isWaitingForResponse { return .yellow }
        return client.isConnected ? .green : .red
    }
}
