import SwiftUI

struct FileDirectoryView: View {
    let path: String
    @Environment(WebSocketClient.self) private var client
    @State private var searchText = ""
    @State private var sortOrder: SortOrder = .nameAZ
    @State private var filterKind: FilterKind = .all

    enum SortOrder: String, CaseIterable {
        case nameAZ = "Name A–Z"
        case nameZA = "Name Z–A"
        case sizeSmall = "Size (smallest)"
        case sizeLarge = "Size (largest)"
    }

    enum FilterKind: String, CaseIterable {
        case all = "All"
        case files = "Files"
        case folders = "Folders"
    }

    private var cacheKey: String { path.isEmpty ? "." : path }

    private var allEntries: [WorkspaceEntry] {
        client.workspaceEntries[cacheKey] ?? []
    }

    private var filteredEntries: [WorkspaceEntry] {
        var entries = allEntries

        switch filterKind {
        case .all: break
        case .files: entries = entries.filter { !$0.is_dir }
        case .folders: entries = entries.filter { $0.is_dir }
        }

        if !searchText.isEmpty {
            entries = entries.filter { $0.name.localizedCaseInsensitiveContains(searchText) }
        }

        switch sortOrder {
        case .nameAZ: entries.sort { $0.name.localizedCompare($1.name) == .orderedAscending }
        case .nameZA: entries.sort { $0.name.localizedCompare($1.name) == .orderedDescending }
        case .sizeSmall: entries.sort { $0.size < $1.size }
        case .sizeLarge: entries.sort { $0.size > $1.size }
        }

        return entries
    }

    private var navigationTitle: String {
        path.isEmpty ? "Files" : URL(fileURLWithPath: path).lastPathComponent
    }

    var body: some View {
        Group {
            if allEntries.isEmpty && client.workspaceEntries[cacheKey] != nil {
                ContentUnavailableView(
                    "Empty Directory",
                    systemImage: "folder",
                    description: Text("This folder has no files.")
                )
            } else {
                List {
                    ForEach(filteredEntries) { entry in
                        let childPath = path.isEmpty ? entry.name : "\(path)/\(entry.name)"
                        NavigationLink(value: childPath) {
                            entryRow(entry)
                        }
                        .contextMenu {
                            Button("Rename") {
                                // TODO: implement rename
                            }
                            Button("Duplicate") {
                                // TODO: implement duplicate
                            }
                            Divider()
                            Button("New File") {
                                // TODO: implement new file
                            }
                            Button("New Folder") {
                                // TODO: implement new folder
                            }
                            Divider()
                            Button("Delete", role: .destructive) {
                                // TODO: implement delete
                            }
                        }
                    }
                }
                .searchable(text: $searchText, prompt: "Search")
            }
        }
        .navigationTitle(navigationTitle)
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .toolbar {
            ToolbarItem(placement: .automatic) {
                Menu {
                    Picker("Sort", selection: $sortOrder) {
                        ForEach(SortOrder.allCases, id: \.self) { order in
                            Text(order.rawValue).tag(order)
                        }
                    }
                    Divider()
                    Picker("Filter", selection: $filterKind) {
                        ForEach(FilterKind.allCases, id: \.self) { kind in
                            Text(kind.rawValue).tag(kind)
                        }
                    }
                } label: {
                    Image(systemName: "line.3.horizontal.decrease.circle")
                }
            }
        }
        .onAppear {
            if client.workspaceEntries[cacheKey] == nil {
                client.listWorkspace(path: path)
            }
        }
        .refreshable {
            client.listWorkspace(path: path)
        }
    }

    private func entryRow(_ entry: WorkspaceEntry) -> some View {
        HStack(spacing: 12) {
            Image(systemName: entry.is_dir ? "folder.fill" : "doc.text")
                .foregroundStyle(entry.is_dir ? .yellow : .secondary)
                .frame(width: 20)

            VStack(alignment: .leading, spacing: 2) {
                Text(entry.name)
                    .foregroundStyle(.primary)
                if !entry.is_dir {
                    Text(formattedSize(entry.size))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    private func formattedSize(_ bytes: Int) -> String {
        let kb = Double(bytes) / 1024
        let mb = kb / 1024
        if mb >= 1 { return String(format: "%.1f MB", mb) }
        if kb >= 1 { return String(format: "%.0f KB", kb) }
        return "\(bytes) B"
    }
}
