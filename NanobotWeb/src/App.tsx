import { useCallback, useState } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { ChatPanel } from './components/ChatPanel';
import { DebugPanel } from './components/DebugPanel';
import { SettingsBar } from './components/SettingsBar';

const DEFAULT_URL = 'ws://100.114.249.118:18790';

function getStoredUrl(): string {
  return localStorage.getItem('serverUrl') || DEFAULT_URL;
}

export default function App() {
  const [serverUrl, setServerUrl] = useState(getStoredUrl);

  const {
    status, messages, frames, waitingForResponse,
    sendMessage, connect, disconnect, resetSession, clearFrames,
  } = useWebSocket(serverUrl);

  const handleUrlChange = useCallback((url: string) => {
    localStorage.setItem('serverUrl', url);
    setServerUrl(url);
  }, []);

  return (
    <div className="app">
      <SettingsBar
        status={status}
        serverUrl={serverUrl}
        messageCount={messages.length}
        frameCount={frames.length}
        onUrlChange={handleUrlChange}
        onResetSession={resetSession}
        onConnect={connect}
        onDisconnect={disconnect}
      />
      <div className="panels">
        <ChatPanel
          messages={messages}
          waitingForResponse={waitingForResponse}
          onSend={sendMessage}
        />
        <DebugPanel frames={frames} onClear={clearFrames} />
      </div>
    </div>
  );
}
