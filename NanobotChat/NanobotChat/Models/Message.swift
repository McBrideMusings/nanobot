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
/// or:               {"type": "history", "messages": [{"role":"user","content":"..."},…]}
/// Fields are optional so unknown message types decode without error.
struct IncomingMessage: Decodable {
    let type: String
    let content: String?
    let id: String?
    let messages: [HistoryEntry]?
}

struct HistoryEntry: Decodable {
    let role: String
    let content: String
}

struct LogEntry: Identifiable {
    let id = UUID()
    let timestamp: Date
    let direction: Direction
    let label: String
    let content: String

    enum Direction: String {
        case send = ">>>"
        case receive = "<<<"
        case system = "---"
    }

    var formatted: String {
        let time = Self.formatter.string(from: timestamp)
        return "\(time) \(direction.rawValue) \(label): \(content)"
    }

    private static let formatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "HH:mm:ss"
        return f
    }()
}
