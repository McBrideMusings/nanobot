import { useCallback, useState } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { usePushNotifications } from './hooks/usePushNotifications';
import { AgentStatusBar } from './components/AgentStatusBar';
import { ChatPanel } from './components/ChatPanel';
import { DebugPanel } from './components/DebugPanel';
import { SettingsBar } from './components/SettingsBar';

const DEFAULT_URL = 'ws://100.114.249.118:18790';

function getStoredUrl(): string {
  return localStorage.getItem('serverUrl') || DEFAULT_URL;
}

function getStoredStreaming(): boolean {
  const v = localStorage.getItem('streamingEnabled');
  return v === null ? true : v === 'true';
}

export default function App() {
  const [serverUrl, setServerUrl] = useState(getStoredUrl);
  const [streamingEnabled, setStreamingEnabled] = useState(getStoredStreaming);

  const {
    status, messages, frames, waitingForResponse,
    agentStatus, agentStatusDetail, events,
    sendMessage, connect, disconnect, resetSession, clearFrames,
    requestLinkPreview, linkPreviews,
  } = useWebSocket(serverUrl, streamingEnabled);

  const push = usePushNotifications({ serverUrl });

  const handleUrlChange = useCallback((url: string) => {
    localStorage.setItem('serverUrl', url);
    setServerUrl(url);
  }, []);

  const handleStreamingToggle = useCallback((enabled: boolean) => {
    localStorage.setItem('streamingEnabled', String(enabled));
    setStreamingEnabled(enabled);
  }, []);

  return (
    <div className="app">
      <SettingsBar
        status={status}
        serverUrl={serverUrl}
        messageCount={messages.length}
        frameCount={frames.length}
        streamingEnabled={streamingEnabled}
        onUrlChange={handleUrlChange}
        onResetSession={resetSession}
        onConnect={connect}
        onDisconnect={disconnect}
        onStreamingToggle={handleStreamingToggle}
        pushSupported={push.isSupported}
        pushSubscribed={push.isSubscribed}
        pushPermission={push.permission}
        onPushToggle={push.isSubscribed ? push.unsubscribe : push.subscribe}
      />
      <AgentStatusBar agentStatus={agentStatus} agentStatusDetail={agentStatusDetail} />
      <div className="panels">
        <ChatPanel
          messages={messages}
          waitingForResponse={waitingForResponse}
          events={events}
          onSend={sendMessage}
          requestLinkPreview={requestLinkPreview}
          linkPreviews={linkPreviews}
        />
        <DebugPanel frames={frames} onClear={clearFrames} />
      </div>
    </div>
  );
}
