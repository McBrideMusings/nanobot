import type { LinkPreviewData } from '../types';

interface Props {
  preview: LinkPreviewData;
}

export function LinkPreview({ preview }: Props) {
  if (!preview.title && !preview.description) return null;

  return (
    <a
      className="link-preview-card"
      href={preview.url}
      target="_blank"
      rel="noopener noreferrer"
    >
      <div className="link-preview-body">
        {preview.favicon && (
          <img
            className="link-preview-favicon"
            src={preview.favicon}
            alt=""
            onError={e => (e.currentTarget.style.display = 'none')}
          />
        )}
        {preview.title && <div className="link-preview-title">{preview.title}</div>}
        {preview.description && (
          <div className="link-preview-desc">{preview.description}</div>
        )}
        <div className="link-preview-url">
          {(() => { try { return new URL(preview.url).hostname; } catch { return preview.url; } })()}
        </div>
      </div>
      {preview.image && (
        <img
          className="link-preview-thumb"
          src={preview.image}
          alt=""
          onError={e => (e.currentTarget.style.display = 'none')}
        />
      )}
    </a>
  );
}
