import SwiftUI

struct MessageBubbleView: View {
    let message: ChatMessage

    var body: some View {
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
