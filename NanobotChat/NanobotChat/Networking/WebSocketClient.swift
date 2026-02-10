import Foundation
import Observation
import os

private let log = Logger(subsystem: "chat.nanobot", category: "WebSocket")

@MainActor
@Observable
final class WebSocketClient {
    var messages: [ChatMessage] = []
    var isConnected = false
    var isWaitingForResponse = false

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

    /// Persistent session ID so the server can resume the same conversation.
    let sessionID: String = {
        if let existing = UserDefaults.standard.string(forKey: "sessionID") {
            return existing
        }
        // Use hex characters only (no hyphens) for a clean URL param
        let id = UUID().uuidString.replacingOccurrences(of: "-", with: "")
            .prefix(12).lowercased()
        UserDefaults.standard.set(String(id), forKey: "sessionID")
        return String(id)
    }()

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

        guard var components = URLComponents(string: serverURL) else {
            log.error("Invalid server URL: \(self.serverURL)")
            return
        }
        var queryItems = components.queryItems ?? []
        queryItems.append(URLQueryItem(name: "session_id", value: sessionID))
        components.queryItems = queryItems

        guard let url = components.url else {
            log.error("Failed to build URL with session_id")
            return
        }

        log.info("Connecting to \(url.absoluteString) session=\(self.sessionID)")
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

        case "response":
            guard let content = incoming.content else { return }
            let botMessage = ChatMessage(content: content, isFromUser: false)
            messages.append(botMessage)
            isWaitingForResponse = false

        default:
            break
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
}
