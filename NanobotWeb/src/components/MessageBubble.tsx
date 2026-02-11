import type { ChatMessage } from '../types';

interface Props {
  message: ChatMessage;
}

export function MessageBubble({ message }: Props) {
  const time = message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div className={`message-bubble ${message.isFromUser ? 'user' : 'bot'}`}>
      <div className="bubble-content">{message.content}</div>
      <div className="bubble-time">{time}</div>
    </div>
  );
}
