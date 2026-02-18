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
    // Workspace fields
    let path: String?
    let entries: [WorkspaceEntry]?
    let success: Bool?
    // Status fields
    let model: String?
    let uptime: Double?
    let host: String?
    let backend: String?
    let gatewayURL: String?
    let capabilities: [String]?

    enum CodingKeys: String, CodingKey {
        case type, content, id, messages, path, entries, success
        case model, uptime, host, backend, capabilities
        case gatewayURL = "gateway_url"
    }
}

struct HistoryEntry: Decodable {
    let role: String
    let content: String
}

struct WorkspaceEntry: Decodable, Identifiable {
    var id: String { name }
    let name: String
    let is_dir: Bool
    let size: Int
}

struct StatusResult {
    let model: String
    let uptimeSeconds: Double
    let host: String
    let backend: String
    let gatewayURL: String
    let capabilities: [String]
    let latencyMs: Double
}

/// Client -> Server: {"type": "workspace_list", "path": "subdir"}
struct OutgoingWorkspaceList: Encodable {
    let type = "workspace_list"
    let path: String
}

/// Client -> Server: {"type": "workspace_read", "path": "file.txt"}
struct OutgoingWorkspaceRead: Encodable {
    let type = "workspace_read"
    let path: String
}

/// Client -> Server: {"type": "workspace_write", "path": "file.txt", "content": "..."}
struct OutgoingWorkspaceWrite: Encodable {
    let type = "workspace_write"
    let path: String
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
