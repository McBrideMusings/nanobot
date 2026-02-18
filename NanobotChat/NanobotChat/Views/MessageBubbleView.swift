import SwiftUI

struct MessageBubbleView: View {
    let message: ChatMessage
    @Environment(AppState.self) private var appState

    var body: some View {
        @Bindable var appState = appState
        VStack(alignment: message.isFromUser ? .trailing : .leading, spacing: 4) {
            HStack {
                if message.isFromUser { Spacer(minLength: 60) }

                Text(message.content)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 8)
                    .background(bubbleColor)
                    .foregroundStyle(message.isFromUser ? .white : .primary)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                    .textSelection(.enabled)

                if !message.isFromUser { Spacer(minLength: 60) }
            }

            if !message.isFromUser, let filePath = extractFilePath(from: message.content) {
                Button {
                    appState.pendingFilePath = filePath
                    appState.selectedTab = .files
                } label: {
                    Label(filePath, systemImage: "doc.text")
                        .font(.caption)
                        .foregroundStyle(Color.accentColor)
                }
                .buttonStyle(.plain)
                .padding(.leading, 14)
            }
        }
    }

    private func extractFilePath(from content: String) -> String? {
        guard let regex = try? NSRegularExpression(pattern: #"\[\[file:([^\]]+)\]\]"#),
              let match = regex.firstMatch(in: content, range: NSRange(content.startIndex..., in: content)),
              let range = Range(match.range(at: 1), in: content) else {
            return nil
        }
        return String(content[range])
    }

    private var bubbleColor: Color {
        if message.isFromUser {
            return .blue
        }
        #if os(iOS)
        return Color(.systemGray5)
        #else
        return Color(nsColor: .controlBackgroundColor)
        #endif
    }
}
