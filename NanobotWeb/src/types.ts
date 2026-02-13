// Wire protocol (matches nanobot/channels/api.py)

export interface OutgoingMessage {
  type: 'message';
  content: string;
}

export interface IncomingResponse {
  type: 'response';
  content: string;
}

export interface IncomingHistory {
  type: 'history';
  messages: { role: string; content: string }[];
}

export interface IncomingError {
  type: 'error';
  content: string;
}

export interface IncomingEvent {
  type: 'event';
  category: string;
  event: string;
  data: Record<string, unknown>;
}

export interface IncomingStreamStart {
  type: 'stream_start';
  id: string;
}

export interface IncomingStreamChunk {
  type: 'stream_chunk';
  id: string;
  delta: string;
}

export interface IncomingStreamEnd {
  type: 'stream_end';
  id: string;
}

export interface IncomingLinkPreviewResult {
  type: 'link_preview_result';
  url: string;
  title?: string;
  description?: string;
  image?: string;
  favicon?: string;
}

export type IncomingMessage =
  | IncomingResponse | IncomingHistory | IncomingError | IncomingEvent
  | IncomingStreamStart | IncomingStreamChunk | IncomingStreamEnd
  | IncomingLinkPreviewResult;

// Agent observability

export type AgentStatus = 'idle' | 'thinking' | 'tool_call' | 'heartbeat' | 'subagent';

export interface AgentEventRecord {
  id: string;
  category: string;
  event: string;
  data: Record<string, unknown>;
  timestamp: Date;
}

// App state

export interface ChatMessage {
  id: string;
  content: string;
  isFromUser: boolean;
  timestamp: Date;
  isStreaming?: boolean;
}

export interface LinkPreviewData {
  url: string;
  title?: string;
  description?: string;
  image?: string;
  favicon?: string;
}

export interface DebugFrame {
  id: string;
  direction: 'in' | 'out';
  raw: string;
  type: string;
  timestamp: Date;
}
