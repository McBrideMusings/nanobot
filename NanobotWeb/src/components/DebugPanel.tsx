import { useCallback, useEffect, useRef, useState } from 'react';
import type { DebugFrame } from '../types';

interface Props {
  frames: DebugFrame[];
  onClear: () => void;
}

function formatLog(f: DebugFrame): string {
  const time = f.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const arrow = f.direction === 'out' ? '>>>' : '<<<';
  const label = f.direction === 'out' ? 'SEND' : f.type.toUpperCase();
  try {
    const parsed = JSON.parse(f.raw);
    const content = parsed.content
      ?? (parsed.messages ? `[${parsed.messages.length} messages]` : f.raw);
    return `${time} ${arrow} ${label}: ${content}`;
  } catch {
    return `${time} ${arrow} ${label}: ${f.raw}`;
  }
}

export function DebugPanel({ frames, onClear }: Props) {
  const preRef = useRef<HTMLPreElement>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (preRef.current) {
      preRef.current.scrollTop = preRef.current.scrollHeight;
    }
  }, [frames]);

  const allLogs = frames.map(formatLog).join('\n');

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(allLogs).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }, [allLogs]);

  return (
    <div className="debug-panel">
      <div className="panel-header">
        Logs
        <div className="log-actions">
          <button className="clear-btn" onClick={handleCopy}>
            {copied ? 'Copied!' : 'Copy All'}
          </button>
          <button className="clear-btn" onClick={onClear}>Clear</button>
        </div>
      </div>
      <pre className="log-view" ref={preRef}>
        {allLogs || 'No logs yet. Connect and send a message.'}
      </pre>
    </div>
  );
}
