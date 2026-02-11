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

export type IncomingMessage = IncomingResponse | IncomingHistory | IncomingError;

// App state

export interface ChatMessage {
  id: string;
  content: string;
  isFromUser: boolean;
  timestamp: Date;
}

export interface DebugFrame {
  id: string;
  direction: 'in' | 'out';
  raw: string;
  type: string;
  timestamp: Date;
}
