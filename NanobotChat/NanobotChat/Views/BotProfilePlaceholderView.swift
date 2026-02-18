import SwiftUI

struct BotProfilePlaceholderView: View {
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ContentUnavailableView(
                "Bot Profile",
                systemImage: "cpu.fill",
                description: Text("Agent profile and configuration coming soon.")
            )
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}
