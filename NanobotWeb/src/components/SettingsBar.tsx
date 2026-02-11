import { useState } from 'react';
import type { ConnectionStatus } from '../hooks/useWebSocket';
import { ConnectionStatus as StatusDisplay } from './ConnectionStatus';

interface Props {
  status: ConnectionStatus;
  serverUrl: string;
  messageCount: number;
  frameCount: number;
  onUrlChange: (url: string) => void;
  onResetSession: () => void;
  onConnect: () => void;
  onDisconnect: () => void;
}

export function SettingsBar({
  status, serverUrl, messageCount, frameCount,
  onUrlChange, onResetSession, onConnect, onDisconnect,
}: Props) {
  const [editing, setEditing] = useState(false);
  const [urlDraft, setUrlDraft] = useState(serverUrl);

  const handleUrlSubmit = () => {
    onUrlChange(urlDraft);
    setEditing(false);
  };

  const handleUrlKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleUrlSubmit();
    if (e.key === 'Escape') { setUrlDraft(serverUrl); setEditing(false); }
  };

  return (
    <div className="settings-bar">
      <div className="settings-top">
        <StatusDisplay status={status} />
        <div className="url-section">
          {editing ? (
            <input
              className="url-input"
              value={urlDraft}
              onChange={e => setUrlDraft(e.target.value)}
              onKeyDown={handleUrlKeyDown}
              onBlur={handleUrlSubmit}
              autoFocus
            />
          ) : (
            <span className="url-display" onClick={() => setEditing(true)} title="Click to edit">
              {serverUrl}
            </span>
          )}
        </div>
        <div className="settings-actions">
          {status === 'disconnected' ? (
            <button onClick={onConnect}>Connect</button>
          ) : (
            <button onClick={onDisconnect}>Disconnect</button>
          )}
          <button onClick={onResetSession}>Clear Chat</button>
        </div>
      </div>
      <div className="settings-bottom">
        <span className="stats">{messageCount} messages | {frameCount} frames</span>
      </div>
    </div>
  );
}
