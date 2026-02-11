import SwiftUI

struct ContentView: View {
    @Environment(WebSocketClient.self) private var client
    @State private var inputText = ""
    @State private var showSettings = false
    @State private var showLogs = false
    @FocusState private var isInputFocused: Bool
    @Environment(\.scenePhase) private var scenePhase

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                messageList
                Divider()
                inputBar
            }
            .navigationTitle("Nanobot")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .navigation) {
                    connectionIndicator
                }
                ToolbarItem(placement: .automatic) {
                    Button { showLogs = true } label: {
                        Image(systemName: "text.alignleft")
                    }
                }
                ToolbarItem(placement: .automatic) {
                    Button { showSettings = true } label: {
                        Image(systemName: "gear")
                    }
                }
            }
            .sheet(isPresented: $showLogs) {
                LogView()
            }
            .sheet(isPresented: $showSettings) {
                SettingsView()
            }
            .onAppear {
                client.connect()
                isInputFocused = true
            }
            .onChange(of: scenePhase) { _, phase in
                if phase == .active && !client.isConnected {
                    client.connect()
                }
            }
        }
    }

    // MARK: - Message List

    private var messageList: some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(client.messages) { message in
                        MessageBubbleView(message: message)
                            .id(message.id.uuidString)
                    }
                    if client.isWaitingForResponse {
                        TypingIndicatorView()
                            .id("typing")
                    }
                }
                .padding()
            }
            .onChange(of: client.messages.count) {
                scrollToBottom(proxy: proxy)
            }
            .onChange(of: client.isWaitingForResponse) {
                scrollToBottom(proxy: proxy)
            }
        }
    }

    private func scrollToBottom(proxy: ScrollViewProxy) {
        let anchor: String? = client.isWaitingForResponse ? "typing" : client.messages.last?.id.uuidString
        if let id = anchor {
            withAnimation(.easeOut(duration: 0.2)) {
                proxy.scrollTo(id, anchor: .bottom)
            }
        }
    }

    // MARK: - Input Bar

    private var inputBar: some View {
        HStack(alignment: .bottom, spacing: 8) {
            TextField("Message", text: $inputText, axis: .vertical)
                .focused($isInputFocused)
                .lineLimit(1...5)
                .textFieldStyle(.plain)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(inputBackground)
                .clipShape(RoundedRectangle(cornerRadius: 20))
                .onSubmit { sendMessage() }

            Button(action: sendMessage) {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.title2)
            }
            .disabled(inputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || !client.isConnected)
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
    }

    private var inputBackground: Color {
        #if os(iOS)
        Color(.systemGray6)
        #else
        Color(nsColor: .textBackgroundColor)
        #endif
    }

    // MARK: - Connection Indicator

    private var connectionIndicator: some View {
        Circle()
            .fill(client.isConnected ? .green : .red)
            .frame(width: 10, height: 10)
    }

    // MARK: - Actions

    private func sendMessage() {
        let text = inputText
        inputText = ""
        client.send(text)
        isInputFocused = true
    }
}

// MARK: - Typing Indicator

struct TypingIndicatorView: View {
    @State private var phase = 0.0

    var body: some View {
        HStack(spacing: 4) {
            ForEach(0..<3, id: \.self) { index in
                Circle()
                    .fill(Color.secondary)
                    .frame(width: 8, height: 8)
                    .offset(y: animationOffset(for: index))
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.leading, 14)
        .onAppear {
            withAnimation(.easeInOut(duration: 0.6).repeatForever(autoreverses: true)) {
                phase = 1.0
            }
        }
    }

    private func animationOffset(for index: Int) -> CGFloat {
        let offset = sin((phase * .pi) + (Double(index) * .pi / 3))
        return CGFloat(offset * -4)
    }
}
