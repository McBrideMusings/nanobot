import { useEffect, useRef } from 'react';
import type { ChatMessage, LinkPreviewData } from '../types';
import { MarkdownRenderer } from './MarkdownRenderer';
import { LinkPreview } from './LinkPreview';

// Match URLs in message content (simple, non-greedy)
const URL_RE = /https?:\/\/[^\s)<>]+/g;

interface Props {
  message: ChatMessage;
  isStreaming?: boolean;
  linkPreviews?: Map<string, LinkPreviewData>;
  requestLinkPreview?: (url: string) => void;
}

export function MessageBubble({ message, isStreaming, linkPreviews, requestLinkPreview }: Props) {
  const time = message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const requestedUrls = useRef(new Set<string>());

  // Extract URLs from bot messages and request previews
  const urls = !message.isFromUser && !isStreaming
    ? [...new Set(message.content.match(URL_RE) || [])]
    : [];

  useEffect(() => {
    if (!requestLinkPreview || urls.length === 0) return;
    for (const url of urls) {
      if (!requestedUrls.current.has(url)) {
        requestedUrls.current.add(url);
        requestLinkPreview(url);
      }
    }
    // requestedUrls ref handles dedup, so content is the correct dep
  }, [message.content, isStreaming, requestLinkPreview]);

  return (
    <div className={`message-bubble ${message.isFromUser ? 'user' : 'bot'}`}>
      <div className="bubble-content">
        {message.isFromUser ? (
          message.content
        ) : (
          <div className="markdown-body">
            <MarkdownRenderer content={message.content} />
            {isStreaming && <span className="streaming-cursor" />}
          </div>
        )}
      </div>
      {urls.length > 0 && linkPreviews && (
        <div className="link-previews">
          {urls.map(url => {
            const preview = linkPreviews.get(url);
            return preview ? <LinkPreview key={url} preview={preview} /> : null;
          })}
        </div>
      )}
      <div className="bubble-time">{time}</div>
    </div>
  );
}
