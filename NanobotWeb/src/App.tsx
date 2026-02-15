import { useCallback, useState } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { usePushNotifications } from './hooks/usePushNotifications';
import { AgentStatusBar } from './components/AgentStatusBar';
import { ChatPanel } from './components/ChatPanel';
import { DebugPanel } from './components/DebugPanel';
import { SettingsBar } from './components/SettingsBar';
import { WorkspacePanel } from './components/WorkspacePanel';
import type { SidebarTab } from './types';

const DEFAULT_URL = 'ws://100.114.249.118:18790';

function getStoredUrl(): string {
  return localStorage.getItem('serverUrl') || DEFAULT_URL;
}

function getStoredStreaming(): boolean {
  const v = localStorage.getItem('streamingEnabled');
  return v === null ? true : v === 'true';
}

function getStoredSidebarTab(): SidebarTab {
  return (localStorage.getItem('sidebarTab') as SidebarTab) || 'debug';
}

function getStoredSidebarOpen(): boolean {
  const v = localStorage.getItem('sidebarOpen');
  return v === null ? true : v === 'true';
}

export default function App() {
  const [serverUrl, setServerUrl] = useState(getStoredUrl);
  const [streamingEnabled, setStreamingEnabled] = useState(getStoredStreaming);
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>(getStoredSidebarTab);
  const [sidebarOpen, setSidebarOpen] = useState(getStoredSidebarOpen);

  const {
    status, messages, frames, waitingForResponse,
    agentStatus, agentStatusDetail, events,
    sendMessage, connect, disconnect, resetSession, clearFrames,
    requestLinkPreview, linkPreviews,
    workspaceEntries, workspaceFileContent, workspaceError, workspaceSaveStatus,
    workspaceList, workspaceRead, workspaceWrite,
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

  const handleTabChange = useCallback((tab: SidebarTab) => {
    localStorage.setItem('sidebarTab', tab);
    setSidebarTab(tab);
    if (!sidebarOpen) {
      localStorage.setItem('sidebarOpen', 'true');
      setSidebarOpen(true);
    }
  }, [sidebarOpen]);

  const handleSidebarClose = useCallback(() => {
    localStorage.setItem('sidebarOpen', 'false');
    setSidebarOpen(false);
  }, []);

  const handleSidebarToggle = useCallback(() => {
    const next = !sidebarOpen;
    localStorage.setItem('sidebarOpen', String(next));
    setSidebarOpen(next);
  }, [sidebarOpen]);

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
      <div className="main-layout">
        <ChatPanel
          messages={messages}
          waitingForResponse={waitingForResponse}
          events={events}
          onSend={sendMessage}
          requestLinkPreview={requestLinkPreview}
          linkPreviews={linkPreviews}
        />
        {sidebarOpen ? (
          <div className="sidebar">
            <div className="sidebar-tabs">
              <button
                className={`sidebar-tab ${sidebarTab === 'debug' ? 'active' : ''}`}
                onClick={() => handleTabChange('debug')}
              >
                Logs
              </button>
              <button
                className={`sidebar-tab ${sidebarTab === 'workspace' ? 'active' : ''}`}
                onClick={() => handleTabChange('workspace')}
              >
                Workspace
              </button>
              <button className="sidebar-close" onClick={handleSidebarClose} title="Close sidebar">
                &times;
              </button>
            </div>
            <div className="sidebar-content">
              {sidebarTab === 'debug' ? (
                <DebugPanel frames={frames} onClear={clearFrames} />
              ) : (
                <WorkspacePanel
                  entries={workspaceEntries}
                  fileContent={workspaceFileContent}
                  error={workspaceError}
                  saveStatus={workspaceSaveStatus}
                  onList={workspaceList}
                  onRead={workspaceRead}
                  onWrite={workspaceWrite}
                />
              )}
            </div>
          </div>
        ) : (
          <button className="sidebar-toggle" onClick={handleSidebarToggle}>
            Sidebar
          </button>
        )}
      </div>
    </div>
  );
}
