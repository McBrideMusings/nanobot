import { useCallback, useState } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { usePushNotifications } from './hooks/usePushNotifications';
import { ActivityBar } from './components/ActivityBar';
import { AgentBar } from './components/AgentBar';
import { TabBar } from './components/TabBar';
import { ChatPanel } from './components/ChatPanel';
import { DebugPanel } from './components/DebugPanel';
import { WorkspacePanel } from './components/WorkspacePanel';
import { TasksPanel } from './components/TasksPanel';
import { CanvasIcon } from './components/Icons';
import type { NavTab } from './types';

const DEFAULT_URL = 'ws://100.114.249.118:18790';

function getStoredUrl(): string {
  return localStorage.getItem('serverUrl') || DEFAULT_URL;
}

function getStoredStreaming(): boolean {
  const v = localStorage.getItem('streamingEnabled');
  return v === null ? true : v === 'true';
}

function getStoredTab(): NavTab {
  return (localStorage.getItem('activeTab') as NavTab) || 'chat';
}

export default function App() {
  const [serverUrl] = useState(getStoredUrl);
  const [streamingEnabled] = useState(getStoredStreaming);
  const [activeTab, setActiveTab] = useState<NavTab>(getStoredTab);

  const {
    status, messages, frames, waitingForResponse,
    agentStatus, agentStatusDetail, events,
    sendMessage, clearFrames,
    requestLinkPreview, linkPreviews,
    workspaceEntries, workspaceFileContent, workspaceError, workspaceSaveStatus,
    workspaceList, workspaceRead, workspaceWrite,
    tasks, taskSession, taskList, taskGetSession,
  } = useWebSocket(serverUrl, streamingEnabled);

  const push = usePushNotifications({ serverUrl });
  // push is still initialized for background notification support
  void push;

  const handleTabChange = useCallback((tab: NavTab) => {
    localStorage.setItem('activeTab', tab);
    setActiveTab(tab);
  }, []);

  const handleOpenProfile = useCallback(() => {
    console.log('Open profile sheet (NB-26)');
  }, []);

  const handleOpenConnection = useCallback(() => {
    console.log('Open connection sheet (NB-25)');
  }, []);

  const handleOpenSettings = useCallback(() => {
    console.log('Open settings sheet (NB-27)');
  }, []);

  return (
    <div className="app">
      <ActivityBar activeTab={activeTab} onTabChange={handleTabChange} />
      <div className="app-main">
        <AgentBar
          agentStatus={agentStatus}
          agentStatusDetail={agentStatusDetail}
          connectionStatus={status}
          onOpenProfile={handleOpenProfile}
          onOpenConnection={handleOpenConnection}
          onOpenSettings={handleOpenSettings}
        />
        <div className="app-view">
          {activeTab === 'chat' && (
            <ChatPanel
              messages={messages}
              waitingForResponse={waitingForResponse}
              events={events}
              onSend={sendMessage}
              requestLinkPreview={requestLinkPreview}
              linkPreviews={linkPreviews}
            />
          )}
          {activeTab === 'canvas' && (
            <div className="canvas-placeholder">
              <CanvasIcon size={48} />
              <h2>Canvas</h2>
              <p>Coming soon</p>
            </div>
          )}
          {activeTab === 'tasks' && (
            <TasksPanel
              tasks={tasks}
              taskSession={taskSession}
              onRequestList={taskList}
              onRequestSession={taskGetSession}
            />
          )}
          {activeTab === 'files' && (
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
          {activeTab === 'logs' && (
            <DebugPanel frames={frames} onClear={clearFrames} />
          )}
        </div>
        <TabBar activeTab={activeTab} onTabChange={handleTabChange} />
      </div>
    </div>
  );
}
