import { useEffect, useRef, useState } from 'react';
import type { ChatMessage } from '../types';
import { MessageBubble } from './MessageBubble';

interface Props {
  messages: ChatMessage[];
  waitingForResponse: boolean;
  onSend: (content: string) => void;
}

export function ChatPanel({ messages, waitingForResponse, onSend }: Props) {
  const [input, setInput] = useState('');
  const listRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, waitingForResponse]);

  const handleSend = () => {
    if (!input.trim()) return;
    onSend(input);
    setInput('');
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize
    const ta = e.target;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
  };

  return (
    <div className="chat-panel">
      <div className="panel-header">Chat</div>
      <div className="message-list" ref={listRef}>
        {messages.map(m => <MessageBubble key={m.id} message={m} />)}
        {waitingForResponse && (
          <div className="message-bubble bot">
            <div className="bubble-content typing">Thinking...</div>
          </div>
        )}
      </div>
      <div className="chat-input-row">
        <textarea
          ref={textareaRef}
          className="chat-input"
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Type a message... (Shift+Enter for newline)"
          rows={1}
        />
        <button className="send-btn" onClick={handleSend} disabled={!input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
