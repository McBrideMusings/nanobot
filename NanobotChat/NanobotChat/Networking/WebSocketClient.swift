import Foundation
import Observation

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

    init() {
        self.session = URLSession(configuration: .default)
    }

    // MARK: - Public API

    func connect() {
        intentionalDisconnect = false
        reconnectDelay = 1.0
        reconnectTask?.cancel()
        reconnectTask = nil

        guard let url = URL(string: serverURL) else { return }

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

        webSocketTask?.send(.string(json)) { [weak self] error in
            if error != nil {
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

        guard let incoming = try? JSONDecoder().decode(IncomingMessage.self, from: data) else { return }

        // Ignore unknown message types (forward-compatible)
        guard incoming.type == "response", let content = incoming.content else { return }

        let botMessage = ChatMessage(content: content, isFromUser: false)
        messages.append(botMessage)
        isWaitingForResponse = false
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
