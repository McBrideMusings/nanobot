import { useCallback, useEffect, useRef, useState } from 'react';
import type {
  AgentEventRecord, AgentStatus, ChatMessage, DebugFrame, IncomingMessage, LinkPreviewData,
  WorkspaceEntry,
} from '../types';

const MAX_FRAMES = 500;
const MAX_EVENTS = 50;
const MAX_RECONNECT_DELAY = 30_000;

function generateId(): string {
  return Math.random().toString(36).slice(2, 14);
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting';

export function useWebSocket(serverUrl: string, streamingEnabled: boolean = true) {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [frames, setFrames] = useState<DebugFrame[]>([]);
  const [waitingForResponse, setWaitingForResponse] = useState(false);
  const [agentStatus, setAgentStatus] = useState<AgentStatus>('idle');
  const [agentStatusDetail, setAgentStatusDetail] = useState('');
  const [events, setEvents] = useState<AgentEventRecord[]>([]);
  const [linkPreviews, setLinkPreviews] = useState<Map<string, LinkPreviewData>>(new Map());

  // Workspace state
  const [workspaceEntries, setWorkspaceEntries] = useState<Map<string, WorkspaceEntry[]>>(new Map());
  const [workspaceFileContent, setWorkspaceFileContent] = useState<{ path: string; content: string } | null>(null);
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);
  const [workspaceSaveStatus, setWorkspaceSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectDelay = useRef(1000);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const intentionalClose = useRef(false);

  // Streaming state tracked via refs to avoid re-renders per chunk
  const streamingMsgId = useRef<string | null>(null);
  const streamBuffer = useRef('');
  const streamingEnabledRef = useRef(streamingEnabled);
  streamingEnabledRef.current = streamingEnabled;
  // Track whether a stream completed for this response cycle (to suppress duplicate 'response')
  const streamDelivered = useRef(false);

  const addFrame = useCallback((direction: 'in' | 'out', raw: string, type: string) => {
    setFrames(prev => {
      const next = [...prev, { id: generateId(), direction, raw, type, timestamp: new Date() }];
      return next.length > MAX_FRAMES ? next.slice(-MAX_FRAMES) : next;
    });
  }, []);

  // Helper to send link preview requests
  const requestLinkPreview = useCallback((url: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const payload = JSON.stringify({ type: 'link_preview', url });
      wsRef.current.send(payload);
    }
  }, []);

  // Workspace send functions
  const workspaceList = useCallback((path: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      setWorkspaceError(null);
      wsRef.current.send(JSON.stringify({ type: 'workspace_list', path }));
    }
  }, []);

  const workspaceRead = useCallback((path: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      setWorkspaceError(null);
      setWorkspaceFileContent(null);
      wsRef.current.send(JSON.stringify({ type: 'workspace_read', path }));
    }
  }, []);

  const workspaceWrite = useCallback((path: string, content: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      setWorkspaceSaveStatus('saving');
      wsRef.current.send(JSON.stringify({ type: 'workspace_write', path, content }));
    }
  }, []);

  const connect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }
    clearTimeout(reconnectTimer.current);
    intentionalClose.current = false;
    reconnectDelay.current = 1000;
    setStatus('connecting');

    const ws = new WebSocket(serverUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('connected');
      reconnectDelay.current = 1000;
    };

    ws.onmessage = (event) => {
      const raw = typeof event.data === 'string' ? event.data : '';
      let parsed: IncomingMessage;
      try {
        parsed = JSON.parse(raw);
      } catch {
        addFrame('in', raw, 'unknown');
        return;
      }

      addFrame('in', raw, parsed.type);

      switch (parsed.type) {
        case 'history': {
          if ('messages' in parsed && parsed.messages) {
            setMessages(parsed.messages.map(m => ({
              id: generateId(),
              content: m.content,
              isFromUser: m.role === 'user',
              timestamp: new Date(),
            })));
          }
          break;
        }
        case 'response': {
          if ('content' in parsed) {
            // If streaming already delivered this message, skip the duplicate
            if (streamDelivered.current) {
              streamDelivered.current = false;
            } else {
              setMessages(prev => [...prev, {
                id: generateId(),
                content: parsed.content,
                isFromUser: false,
                timestamp: new Date(),
              }]);
            }
            setWaitingForResponse(false);
            setAgentStatus('idle');
            setAgentStatusDetail('');
            setEvents([]);
          }
          break;
        }
        case 'error': {
          if ('content' in parsed) {
            setMessages(prev => [...prev, {
              id: generateId(),
              content: `Error: ${parsed.content}`,
              isFromUser: false,
              timestamp: new Date(),
            }]);
            setWaitingForResponse(false);
            setAgentStatus('idle');
            setAgentStatusDetail('');
          }
          break;
        }

        // --- Streaming messages ---
        case 'stream_start': {
          streamingMsgId.current = parsed.id;
          streamBuffer.current = '';
          if (streamingEnabledRef.current) {
            // Create a placeholder message for progressive rendering
            const msgId = `stream-${parsed.id}`;
            setMessages(prev => [...prev, {
              id: msgId,
              content: '',
              isFromUser: false,
              timestamp: new Date(),
              isStreaming: true,
            }]);
            setWaitingForResponse(false);
          }
          break;
        }
        case 'stream_chunk': {
          if (parsed.id !== streamingMsgId.current) break;
          streamBuffer.current += parsed.delta;
          if (streamingEnabledRef.current) {
            const accumulated = streamBuffer.current;
            const msgId = `stream-${parsed.id}`;
            setMessages(prev =>
              prev.map(m => m.id === msgId ? { ...m, content: accumulated } : m)
            );
          }
          break;
        }
        case 'stream_end': {
          if (parsed.id !== streamingMsgId.current) break;
          const finalContent = streamBuffer.current;
          const msgId = `stream-${parsed.id}`;
          streamingMsgId.current = null;
          streamBuffer.current = '';
          streamDelivered.current = true;

          if (streamingEnabledRef.current) {
            // Mark the streaming message as complete
            setMessages(prev =>
              prev.map(m => m.id === msgId
                ? { ...m, content: finalContent, isStreaming: false }
                : m
              )
            );
          } else {
            // Non-streaming mode: show the full message at once
            setMessages(prev => [...prev, {
              id: msgId,
              content: finalContent,
              isFromUser: false,
              timestamp: new Date(),
            }]);
          }
          // Don't reset waitingForResponse here — the 'response' message
          // from the bus still handles that (stream_end fires mid-loop
          // when tool calls follow). The final 'response' resets everything.
          break;
        }

        case 'link_preview_result': {
          const preview: LinkPreviewData = {
            url: parsed.url,
            title: parsed.title,
            description: parsed.description,
            image: parsed.image,
            favicon: parsed.favicon,
          };
          setLinkPreviews(prev => new Map(prev).set(parsed.url, preview));
          break;
        }

        case 'workspace_list_result': {
          if (parsed.error) {
            setWorkspaceError(parsed.error);
          } else {
            setWorkspaceEntries(prev => new Map(prev).set(parsed.path, parsed.entries));
            setWorkspaceError(null);
          }
          break;
        }

        case 'workspace_read_result': {
          if (parsed.error) {
            setWorkspaceError(parsed.error);
          } else {
            setWorkspaceFileContent({ path: parsed.path, content: parsed.content });
            setWorkspaceError(null);
          }
          break;
        }

        case 'workspace_write_result': {
          if (parsed.error) {
            setWorkspaceSaveStatus('error');
            setWorkspaceError(parsed.error);
          } else {
            setWorkspaceSaveStatus('saved');
            setWorkspaceError(null);
            setTimeout(() => setWorkspaceSaveStatus('idle'), 2000);
          }
          break;
        }

        case 'event': {
          if ('category' in parsed && 'event' in parsed) {
            const record: AgentEventRecord = {
              id: generateId(),
              category: parsed.category,
              event: parsed.event,
              data: parsed.data ?? {},
              timestamp: new Date(),
            };
            setEvents(prev => {
              const next = [...prev, record];
              return next.length > MAX_EVENTS ? next.slice(-MAX_EVENTS) : next;
            });

            // Update agent status based on event type
            if (parsed.category === 'agent') {
              switch (parsed.event) {
                case 'thinking_started':
                  setAgentStatus('thinking');
                  setAgentStatusDetail('');
                  break;
                case 'tool_call':
                  setAgentStatus('tool_call');
                  setAgentStatusDetail(String(parsed.data?.name ?? ''));
                  break;
                case 'thinking_finished':
                  // Reset everything — covers both user-initiated and
                  // background processing (heartbeat, cron) that don't
                  // produce a WebSocket "response" frame.
                  setWaitingForResponse(false);
                  setAgentStatus('idle');
                  setAgentStatusDetail('');
                  setEvents([]);
                  break;
              }
            } else if (parsed.category === 'heartbeat') {
              setAgentStatus('heartbeat');
              setAgentStatusDetail(String(parsed.data?.summary ?? ''));
            } else if (parsed.category === 'subagent') {
              if (parsed.event === 'spawned') {
                setAgentStatus('subagent');
                setAgentStatusDetail(String(parsed.data?.label ?? ''));
              } else if (parsed.event === 'completed') {
                setAgentStatus('idle');
                setAgentStatusDetail('');
              }
            }
          }
          break;
        }
      }
    };

    ws.onclose = () => {
      setStatus('disconnected');
      setWaitingForResponse(false);
      setAgentStatus('idle');
      setAgentStatusDetail('');
      setEvents([]);
      wsRef.current = null;

      if (!intentionalClose.current) {
        const delay = reconnectDelay.current;
        reconnectDelay.current = Math.min(reconnectDelay.current * 2, MAX_RECONNECT_DELAY);
        reconnectTimer.current = setTimeout(connect, delay);
      }
    };

    ws.onerror = () => {
      // onclose will fire after this
    };
  }, [serverUrl, addFrame]);

  const disconnect = useCallback(() => {
    intentionalClose.current = true;
    clearTimeout(reconnectTimer.current);
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStatus('disconnected');
    setWaitingForResponse(false);
  }, []);

  const sendMessage = useCallback((content: string) => {
    const trimmed = content.trim();
    if (!trimmed || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const payload = JSON.stringify({ type: 'message', content: trimmed });
    wsRef.current.send(payload);
    addFrame('out', payload, 'message');

    setMessages(prev => [...prev, {
      id: generateId(),
      content: trimmed,
      isFromUser: true,
      timestamp: new Date(),
    }]);
    setWaitingForResponse(true);
    streamDelivered.current = false;
  }, [addFrame]);

  const resetSession = useCallback(() => {
    disconnect();
    setMessages([]);
    setFrames([]);
  }, [disconnect]);

  const clearFrames = useCallback(() => {
    setFrames([]);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return () => {
      intentionalClose.current = true;
      clearTimeout(reconnectTimer.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    status,
    messages,
    frames,
    waitingForResponse,
    agentStatus,
    agentStatusDetail,
    events,
    sendMessage,
    connect,
    disconnect,
    resetSession,
    clearFrames,
    requestLinkPreview,
    linkPreviews,
    workspaceEntries,
    workspaceFileContent,
    workspaceError,
    workspaceSaveStatus,
    workspaceList,
    workspaceRead,
    workspaceWrite,
  };
}
