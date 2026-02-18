import SwiftUI

struct CanvasPlaceholderView: View {
    var body: some View {
        ContentUnavailableView(
            "Canvas",
            systemImage: "rectangle.on.rectangle",
            description: Text("Visual canvas coming soon.")
        )
    }
}
