import { useCallback, useEffect, useState } from 'react';
import { FileBrowser } from './FileBrowser';
import { FileEditor } from './FileEditor';
import type { WorkspaceEntry } from '../types';

interface WorkspacePanelProps {
  entries: Map<string, WorkspaceEntry[]>;
  fileContent: { path: string; content: string } | null;
  error: string | null;
  saveStatus: 'idle' | 'saving' | 'saved' | 'error';
  onList: (path: string) => void;
  onRead: (path: string) => void;
  onWrite: (path: string, content: string) => void;
}

export function WorkspacePanel({
  entries, fileContent, error, saveStatus,
  onList, onRead, onWrite,
}: WorkspacePanelProps) {
  const [currentPath, setCurrentPath] = useState('');
  const [editingFile, setEditingFile] = useState<string | null>(null);

  // Load root directory on mount
  useEffect(() => {
    if (!entries.has('.')) {
      onList('');
    }
  }, [entries, onList]);

  const handleNavigate = useCallback((path: string) => {
    setCurrentPath(path);
    const key = path || '.';
    if (!entries.has(key)) {
      onList(path);
    }
  }, [entries, onList]);

  const handleFileSelect = useCallback((path: string) => {
    setEditingFile(path);
    onRead(path);
  }, [onRead]);

  const handleEditorClose = useCallback(() => {
    setEditingFile(null);
  }, []);

  // Resolve entries for current path (server returns "." for root)
  const listKey = currentPath || '.';
  const currentEntries = entries.get(listKey) ?? [];

  if (editingFile) {
    const loadedContent = fileContent && fileContent.path === editingFile ? fileContent.content : null;
    return (
      <div className="workspace-panel">
        <FileEditor
          path={editingFile}
          content={loadedContent}
          saveStatus={saveStatus}
          error={error}
          onSave={onWrite}
          onClose={handleEditorClose}
        />
      </div>
    );
  }

  return (
    <div className="workspace-panel">
      <FileBrowser
        currentPath={currentPath}
        entries={currentEntries}
        error={error}
        onNavigate={handleNavigate}
        onFileSelect={handleFileSelect}
      />
    </div>
  );
}
