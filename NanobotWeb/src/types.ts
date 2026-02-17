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

// Workspace messages

export interface WorkspaceEntry {
  name: string;
  is_dir: boolean;
  size: number;
}

export interface OutgoingWorkspaceList {
  type: 'workspace_list';
  path: string;
}

export interface OutgoingWorkspaceRead {
  type: 'workspace_read';
  path: string;
}

export interface OutgoingWorkspaceWrite {
  type: 'workspace_write';
  path: string;
  content: string;
}

export interface IncomingWorkspaceListResult {
  type: 'workspace_list_result';
  path: string;
  entries: WorkspaceEntry[];
  error?: string;
}

export interface IncomingWorkspaceReadResult {
  type: 'workspace_read_result';
  path: string;
  content: string;
  error?: string;
}

export interface IncomingWorkspaceWriteResult {
  type: 'workspace_write_result';
  path: string;
  success: boolean;
  error?: string;
}

export type NavTab = 'chat' | 'canvas' | 'files' | 'tasks' | 'logs';

// Task types

export interface TaskRecord {
  id: string;
  type: 'heartbeat' | 'cron';
  status: 'running' | 'completed' | 'failed';
  label: string;
  summary: string;
  createdAtMs: number;
  completedAtMs: number | null;
  error: string | null;
}

export interface IncomingTaskListResult {
  type: 'task_list_result';
  tasks: TaskRecord[];
}

export interface IncomingTaskSessionResult {
  type: 'task_session_result';
  task_id: string;
  messages: { role: string; content: string }[];
}

export interface IncomingTaskEvent {
  type: 'task_event';
  event: string;
  data: Record<string, unknown>;
}

export interface IncomingSystemMessage {
  type: 'system_message';
  task_id: string;
  content: string;
}

export type IncomingMessage =
  | IncomingResponse | IncomingHistory | IncomingError | IncomingEvent
  | IncomingStreamStart | IncomingStreamChunk | IncomingStreamEnd
  | IncomingLinkPreviewResult
  | IncomingWorkspaceListResult | IncomingWorkspaceReadResult | IncomingWorkspaceWriteResult
  | IncomingTaskListResult | IncomingTaskSessionResult | IncomingTaskEvent | IncomingSystemMessage;

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
  isSystem?: boolean;
  taskId?: string;
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
