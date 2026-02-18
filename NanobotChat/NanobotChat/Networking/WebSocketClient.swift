import Foundation
import Observation
import os

private let log = Logger(subsystem: "chat.nanobot", category: "WebSocket")

@MainActor
@Observable
final class WebSocketClient {
    var messages: [ChatMessage] = []
    var logEntries: [LogEntry] = []
    var isConnected = false
    var isWaitingForResponse = false

    // Workspace state
    var workspaceEntries: [String: [WorkspaceEntry]] = [:]
    var workspaceFileContent: (path: String, content: String)? = nil
    var workspaceSaveStatus: SaveStatus = .idle

    enum SaveStatus { case idle, saving, saved, error }

    private var webSocketTask: URLSessionWebSocketTask?
    private var session: URLSession
    private var receiveTask: Task<Void, Never>?
    private var pingTask: Task<Void, Never>?
    private var reconnectTask: Task<Void, Never>?
    private var intentionalDisconnect = false
    private var reconnectDelay: TimeInterval = 1.0

    private static let defaultURL = "ws://100.114.249.118:18790"
    private static let maxReconnectDelay: TimeInterval = 30.0
    private static let pingInterval: TimeInterval = 15.0

    var serverURL: String {
        UserDefaults.standard.string(forKey: "serverURL") ?? Self.defaultURL
    }

    init() {
        self.session = URLSession(configuration: .default)
    }

    // MARK: - Public API

    func connect() {
        // Tear down any existing connection first
        cancelTasks()
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil

        intentionalDisconnect = false
        reconnectDelay = 1.0
        reconnectTask?.cancel()
        reconnectTask = nil

        guard let url = URL(string: serverURL) else {
            log.error("Invalid server URL: \(self.serverURL)")
            return
        }

        addLog(.system, "CONNECT", serverURL)
        log.info("Connecting to \(url.absoluteString)")
        let task = session.webSocketTask(with: url)
        webSocketTask = task
        task.resume()
        isConnected = true

        startReceiving()
        startPingLoop()
    }

    func disconnect() {
        intentionalDisconnect = true
        cancelTasks()
        webSocketTask?.cancel(with: .normalClosure, reason: nil)
        webSocketTask = nil
        isConnected = false
        isWaitingForResponse = false
        addLog(.system, "DISCONNECT", "Closed by user")
    }

    func send(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        let userMessage = ChatMessage(content: trimmed, isFromUser: true)
        messages.append(userMessage)
        isWaitingForResponse = true

        let outgoing = OutgoingMessage(content: trimmed)
        guard let data = try? JSONEncoder().encode(outgoing),
              let json = String(data: data, encoding: .utf8) else { return }

        addLog(.send, "SEND", trimmed)
        log.info("Sending: \(json)")
        webSocketTask?.send(.string(json)) { [weak self] error in
            if let error {
                log.error("Send failed: \(error.localizedDescription)")
                Task { @MainActor in
                    self?.handleDisconnect()
                }
            }
        }
    }

    func clearLogs() {
        logEntries.removeAll()
    }

    // MARK: - Workspace

    func listWorkspace(path: String = "") {
        sendJSON(OutgoingWorkspaceList(path: path))
        addLog(.send, "WORKSPACE_LIST", path.isEmpty ? "." : path)
    }

    func readFile(path: String) {
        sendJSON(OutgoingWorkspaceRead(path: path))
        addLog(.send, "WORKSPACE_READ", path)
    }

    func writeFile(path: String, content: String) {
        workspaceSaveStatus = .saving
        sendJSON(OutgoingWorkspaceWrite(path: path, content: content))
        addLog(.send, "WORKSPACE_WRITE", path)
    }

    func testConnection(url: String) async -> (latencyMs: Double, result: StatusResult?) {
        guard let wsURL = URL(string: url) else { return (0, nil) }
        let testSession = URLSession(configuration: .ephemeral)
        let task = testSession.webSocketTask(with: wsURL)
        task.resume()
        let start = Date()
        do {
            try await task.send(.string(#"{"type":"status"}"#))
            let message = try await task.receive()
            let latency = Date().timeIntervalSince(start) * 1000
            task.cancel(with: .normalClosure, reason: nil)
            let data: Data
            switch message {
            case .string(let text): data = Data(text.utf8)
            case .data(let d): data = d
            @unknown default: return (latency, nil)
            }
            guard let incoming = try? JSONDecoder().decode(IncomingMessage.self, from: data),
                  incoming.type == "status_result" else {
                return (latency, nil)
            }
            let result = StatusResult(
                model: incoming.model ?? "",
                uptimeSeconds: incoming.uptime ?? 0,
                host: incoming.host ?? "",
                backend: incoming.backend ?? "",
                gatewayURL: incoming.gatewayURL ?? "",
                capabilities: incoming.capabilities ?? [],
                latencyMs: latency
            )
            return (latency, result)
        } catch {
            task.cancel(with: .abnormalClosure, reason: nil)
            return (0, nil)
        }
    }

    // MARK: - Receive Loop

    private func startReceiving() {
        receiveTask?.cancel()
        receiveTask = Task { [weak self] in
            guard let self else { return }
            while !Task.isCancelled {
                do {
                    guard let message = try await self.webSocketTask?.receive() else { break }
                    self.handleMessage(message)
                } catch {
                    if !Task.isCancelled {
                        log.error("Receive error: \(error.localizedDescription)")
                        self.handleDisconnect()
                    }
                    break
                }
            }
        }
    }

    private func handleMessage(_ message: URLSessionWebSocketTask.Message) {
        let data: Data
        switch message {
        case .string(let text):
            guard let d = text.data(using: .utf8) else { return }
            data = d
        case .data(let d):
            data = d
        @unknown default:
            return
        }

        guard let incoming = try? JSONDecoder().decode(IncomingMessage.self, from: data) else {
            log.warning("Failed to decode incoming message")
            addLog(.receive, "ERROR", "Failed to decode message")
            return
        }

        log.info("Received message type=\(incoming.type)")

        switch incoming.type {
        case "history":
            guard let entries = incoming.messages else { return }
            log.info("Restoring \(entries.count) history messages")
            messages = entries.map { entry in
                ChatMessage(content: entry.content, isFromUser: entry.role == "user")
            }
            addLog(.receive, "HISTORY", "[\(entries.count) messages]")

        case "response":
            guard let content = incoming.content else { return }
            let botMessage = ChatMessage(content: content, isFromUser: false)
            messages.append(botMessage)
            isWaitingForResponse = false
            addLog(.receive, "RESPONSE", content)

        case "error":
            let content = incoming.content ?? "Unknown error"
            addLog(.receive, "ERROR", content)

        case "workspace_list_result":
            let key = incoming.path ?? "."
            workspaceEntries[key] = incoming.entries ?? []
            addLog(.receive, "WORKSPACE_LIST", key)

        case "workspace_read_result":
            if let path = incoming.path, let content = incoming.content {
                workspaceFileContent = (path: path, content: content)
                addLog(.receive, "WORKSPACE_READ", path)
            }

        case "workspace_write_result":
            workspaceSaveStatus = (incoming.success == true) ? .saved : .error
            addLog(.receive, "WORKSPACE_WRITE", incoming.path ?? "")

        default:
            addLog(.receive, incoming.type.uppercased(), incoming.content ?? "")
        }
    }

    // MARK: - Helpers

    private func sendJSON<T: Encodable>(_ value: T) {
        guard let data = try? JSONEncoder().encode(value),
              let json = String(data: data, encoding: .utf8) else { return }
        webSocketTask?.send(.string(json)) { [weak self] error in
            if let error {
                log.error("Send failed: \(error.localizedDescription)")
                Task { @MainActor in self?.handleDisconnect() }
            }
        }
    }

    // MARK: - Ping Loop

    private func startPingLoop() {
        pingTask?.cancel()
        pingTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(Self.pingInterval))
                guard !Task.isCancelled else { break }
                self?.webSocketTask?.sendPing { error in
                    if error != nil {
                        Task { @MainActor in
                            self?.handleDisconnect()
                        }
                    }
                }
            }
        }
    }

    // MARK: - Reconnection

    private func handleDisconnect() {
        guard isConnected else { return }
        log.warning("Disconnected from server")
        addLog(.system, "DISCONNECT", "Connection lost, reconnecting...")
        cancelTasks()
        webSocketTask?.cancel(with: .abnormalClosure, reason: nil)
        webSocketTask = nil
        isConnected = false
        isWaitingForResponse = false
        scheduleReconnect()
    }

    private func scheduleReconnect() {
        guard !intentionalDisconnect else { return }

        let delay = reconnectDelay
        reconnectDelay = min(reconnectDelay * 2, Self.maxReconnectDelay)

        reconnectTask?.cancel()
        reconnectTask = Task { [weak self] in
            try? await Task.sleep(for: .seconds(delay))
            guard !Task.isCancelled else { return }
            self?.connect()
        }
    }

    private func cancelTasks() {
        receiveTask?.cancel()
        receiveTask = nil
        pingTask?.cancel()
        pingTask = nil
    }

    // MARK: - Logging

    private func addLog(_ direction: LogEntry.Direction, _ label: String, _ content: String) {
        logEntries.append(LogEntry(timestamp: Date(), direction: direction, label: label, content: content))
    }
}
