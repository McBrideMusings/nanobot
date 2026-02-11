import { useCallback, useEffect, useRef, useState } from 'react';
import type { ChatMessage, DebugFrame, IncomingMessage } from '../types';

const MAX_FRAMES = 500;
const MAX_RECONNECT_DELAY = 30_000;

function generateId(): string {
  return Math.random().toString(36).slice(2, 14);
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting';

export function useWebSocket(serverUrl: string) {
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [frames, setFrames] = useState<DebugFrame[]>([]);
  const [waitingForResponse, setWaitingForResponse] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectDelay = useRef(1000);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const intentionalClose = useRef(false);

  const addFrame = useCallback((direction: 'in' | 'out', raw: string, type: string) => {
    setFrames(prev => {
      const next = [...prev, { id: generateId(), direction, raw, type, timestamp: new Date() }];
      return next.length > MAX_FRAMES ? next.slice(-MAX_FRAMES) : next;
    });
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
            setMessages(prev => [...prev, {
              id: generateId(),
              content: parsed.content,
              isFromUser: false,
              timestamp: new Date(),
            }]);
            setWaitingForResponse(false);
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
          }
          break;
        }
      }
    };

    ws.onclose = () => {
      setStatus('disconnected');
      setWaitingForResponse(false);
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
    sendMessage,
    connect,
    disconnect,
    resetSession,
    clearFrames,
  };
}
