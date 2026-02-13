import { useState } from 'react';
import type { ConnectionStatus } from '../hooks/useWebSocket';
import { ConnectionStatus as StatusDisplay } from './ConnectionStatus';

interface Props {
  status: ConnectionStatus;
  serverUrl: string;
  messageCount: number;
  frameCount: number;
  streamingEnabled: boolean;
  onUrlChange: (url: string) => void;
  onResetSession: () => void;
  onConnect: () => void;
  onDisconnect: () => void;
  onStreamingToggle: (enabled: boolean) => void;
  pushSupported: boolean;
  pushSubscribed: boolean;
  pushPermission: NotificationPermission;
  onPushToggle: () => void;
}

export function SettingsBar({
  status, serverUrl, messageCount, frameCount, streamingEnabled,
  onUrlChange, onResetSession, onConnect, onDisconnect, onStreamingToggle,
  pushSupported, pushSubscribed, pushPermission, onPushToggle,
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

  const pushTitle = !pushSupported
    ? 'Push notifications not supported (requires HTTPS)'
    : pushPermission === 'denied'
      ? 'Notification permission denied'
      : pushSubscribed
        ? 'Click to unsubscribe from push notifications'
        : 'Click to enable push notifications';

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
          <label className="toggle-label" title="Toggle streaming responses">
            <input
              type="checkbox"
              checked={streamingEnabled}
              onChange={e => onStreamingToggle(e.target.checked)}
            />
            Stream
          </label>
          {pushSupported && (
            <label
              className="toggle-label"
              title={pushTitle}
            >
              <input
                type="checkbox"
                checked={pushSubscribed}
                onChange={onPushToggle}
                disabled={pushPermission === 'denied'}
              />
              Push
            </label>
          )}
        </div>
      </div>
      <div className="settings-bottom">
        <span className="stats">{messageCount} messages | {frameCount} frames</span>
      </div>
    </div>
  );
}
