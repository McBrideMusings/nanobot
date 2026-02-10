import Foundation

struct ChatMessage: Identifiable, Equatable {
    let id: UUID
    let content: String
    let isFromUser: Bool
    let timestamp: Date

    init(content: String, isFromUser: Bool) {
        self.id = UUID()
        self.content = content
        self.isFromUser = isFromUser
        self.timestamp = Date()
    }
}

/// Client -> Server: {"type": "message", "content": "hello"}
struct OutgoingMessage: Encodable {
    let type = "message"
    let content: String
}

/// Server -> Client: {"type": "response", "content": "Hi!", "id": "msg_abc123"}
/// Fields are optional so unknown message types decode without error.
struct IncomingMessage: Decodable {
    let type: String
    let content: String?
    let id: String?
}
