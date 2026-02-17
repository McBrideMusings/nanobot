import { useEffect, useState } from 'react';
import type { TaskRecord } from '../types';
import { MarkdownRenderer } from './MarkdownRenderer';

function timeAgo(ms: number): string {
  const seconds = Math.floor((Date.now() - ms) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

interface Props {
  tasks: TaskRecord[];
  taskSession: { taskId: string; messages: { role: string; content: string }[] } | null;
  onRequestList: () => void;
  onRequestSession: (taskId: string) => void;
}

export function TasksPanel({ tasks, taskSession, onRequestList, onRequestSession }: Props) {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  // Request task list on mount
  useEffect(() => {
    onRequestList();
  }, [onRequestList]);

  const selectedTask = selectedTaskId ? tasks.find(t => t.id === selectedTaskId) : null;

  if (selectedTaskId && selectedTask) {
    return (
      <div className="tasks-panel">
        <div className="task-detail-header">
          <button className="file-editor-back" onClick={() => setSelectedTaskId(null)}>Back</button>
          <span className="task-detail-title">{selectedTask.label}</span>
          <span className={`task-dot task-dot-${selectedTask.status}`} />
        </div>
        <div className="task-detail-meta">
          <span>{selectedTask.type}</span>
          <span>{timeAgo(selectedTask.createdAtMs)}</span>
          {selectedTask.summary && <span>{selectedTask.summary}</span>}
          {selectedTask.error && <span className="task-error">{selectedTask.error}</span>}
        </div>
        <div className="task-detail-messages">
          {taskSession && taskSession.taskId === selectedTaskId ? (
            taskSession.messages.length > 0 ? (
              taskSession.messages.map((m, i) => (
                <div key={i} className={`task-msg task-msg-${m.role}`}>
                  <div className="task-msg-role">{m.role}</div>
                  <div className="task-msg-content markdown-body">
                    <MarkdownRenderer content={m.content} />
                  </div>
                </div>
              ))
            ) : (
              <div className="task-detail-empty">No session messages</div>
            )
          ) : (
            <div className="task-detail-empty">Loading session...</div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="tasks-panel">
      <div className="panel-header">Tasks</div>
      {tasks.length === 0 ? (
        <div className="tasks-empty">No tasks yet</div>
      ) : (
        <div className="task-list">
          {tasks.map(task => (
            <button
              key={task.id}
              className="task-list-item"
              onClick={() => {
                setSelectedTaskId(task.id);
                onRequestSession(task.id);
              }}
            >
              <span className={`task-dot task-dot-${task.status}`} />
              <div className="task-list-item-body">
                <div className="task-list-item-label">{task.label}</div>
                {task.summary && (
                  <div className="task-list-item-summary">{task.summary}</div>
                )}
              </div>
              <span className="task-list-item-time">{timeAgo(task.createdAtMs)}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
