import type { WorkspaceEntry } from '../types';

interface FileBrowserProps {
  currentPath: string;
  entries: WorkspaceEntry[];
  error: string | null;
  onNavigate: (path: string) => void;
  onFileSelect: (path: string) => void;
}

function formatSize(bytes: number): string {
  if (bytes === 0) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileBrowser({ currentPath, entries, error, onNavigate, onFileSelect }: FileBrowserProps) {
  const segments = currentPath ? currentPath.split('/').filter(Boolean) : [];

  const handleBreadcrumb = (index: number) => {
    if (index < 0) {
      onNavigate('');
    } else {
      onNavigate(segments.slice(0, index + 1).join('/'));
    }
  };

  const handleEntryClick = (entry: WorkspaceEntry) => {
    const childPath = currentPath ? `${currentPath}/${entry.name}` : entry.name;
    if (entry.is_dir) {
      onNavigate(childPath);
    } else {
      onFileSelect(childPath);
    }
  };

  return (
    <div className="file-browser">
      <div className="file-browser-header">
        <div className="file-breadcrumb">
          <span
            className={`breadcrumb-segment ${segments.length === 0 ? 'active' : ''}`}
            onClick={() => handleBreadcrumb(-1)}
          >
            workspace
          </span>
          {segments.map((seg, i) => (
            <span key={i}>
              <span className="breadcrumb-sep">/</span>
              <span
                className={`breadcrumb-segment ${i === segments.length - 1 ? 'active' : ''}`}
                onClick={() => handleBreadcrumb(i)}
              >
                {seg}
              </span>
            </span>
          ))}
        </div>
      </div>

      {error && <div className="workspace-error">{error}</div>}

      <div className="file-list">
        {segments.length > 0 && (
          <div
            className="file-entry file-entry-up"
            onClick={() => handleBreadcrumb(segments.length - 2)}
          >
            <span className="file-icon">&#8617;</span>
            <span className="file-name">..</span>
          </div>
        )}
        {entries.map(entry => (
          <div
            key={entry.name}
            className={`file-entry ${entry.is_dir ? 'file-entry-dir' : 'file-entry-file'}`}
            onClick={() => handleEntryClick(entry)}
          >
            <span className="file-icon">{entry.is_dir ? '\uD83D\uDCC1' : '\uD83D\uDCC4'}</span>
            <span className="file-name">{entry.name}</span>
            {!entry.is_dir && <span className="file-size">{formatSize(entry.size)}</span>}
          </div>
        ))}
        {entries.length === 0 && !error && (
          <div className="file-entry file-entry-empty">Empty directory</div>
        )}
      </div>
    </div>
  );
}
