import { useCallback, useEffect, useRef, useState } from 'react';
import { EditorState } from '@codemirror/state';
import { EditorView, keymap, lineNumbers, drawSelection } from '@codemirror/view';
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands';
import { syntaxHighlighting, defaultHighlightStyle } from '@codemirror/language';
import { markdown } from '@codemirror/lang-markdown';
import { json as jsonLang } from '@codemirror/lang-json';

interface FileEditorProps {
  path: string;
  content: string | null;
  saveStatus: 'idle' | 'saving' | 'saved' | 'error';
  error: string | null;
  onSave: (path: string, content: string) => void;
  onClose: () => void;
}

const darkTheme = EditorView.theme({
  '&': {
    backgroundColor: 'var(--bg)',
    color: 'var(--text)',
    height: '100%',
  },
  '.cm-content': {
    fontFamily: "'SF Mono', 'Fira Code', 'Consolas', monospace",
    fontSize: '13px',
    lineHeight: '1.6',
    caretColor: 'var(--accent)',
  },
  '.cm-cursor': { borderLeftColor: 'var(--accent)' },
  '&.cm-focused .cm-selectionBackground, .cm-selectionBackground': {
    backgroundColor: 'rgba(74, 158, 255, 0.25)',
  },
  '.cm-gutters': {
    backgroundColor: 'var(--surface)',
    color: 'var(--text-dim)',
    border: 'none',
    borderRight: '1px solid var(--border)',
  },
  '.cm-activeLineGutter': { backgroundColor: 'var(--surface2)' },
  '.cm-activeLine': { backgroundColor: 'rgba(255, 255, 255, 0.03)' },
}, { dark: true });

function getLanguage(path: string) {
  if (path.endsWith('.json')) return jsonLang();
  return markdown();
}

const statusLabels: Record<string, string> = {
  idle: '',
  saving: 'Saving...',
  saved: 'Saved',
  error: 'Save failed',
};

export function FileEditor({ path, content, saveStatus, error, onSave, onClose }: FileEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);
  const [dirty, setDirty] = useState(false);
  const pathRef = useRef(path);
  pathRef.current = path;

  const handleSave = useCallback(() => {
    if (viewRef.current) {
      onSave(pathRef.current, viewRef.current.state.doc.toString());
      setDirty(false);
    }
  }, [onSave]);

  // Set up CodeMirror
  useEffect(() => {
    if (!editorRef.current || content === null) return;

    const saveKeymap = keymap.of([{
      key: 'Mod-s',
      run: () => {
        if (viewRef.current) {
          onSave(pathRef.current, viewRef.current.state.doc.toString());
          setDirty(false);
        }
        return true;
      },
    }]);

    const state = EditorState.create({
      doc: content,
      extensions: [
        lineNumbers(),
        drawSelection(),
        history(),
        syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
        getLanguage(path),
        darkTheme,
        saveKeymap,
        keymap.of([...defaultKeymap, ...historyKeymap]),
        EditorView.updateListener.of(update => {
          if (update.docChanged) setDirty(true);
        }),
      ],
    });

    const view = new EditorView({ state, parent: editorRef.current });
    viewRef.current = view;

    return () => {
      view.destroy();
      viewRef.current = null;
    };
    // Only re-create on path/content change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, content]);

  const filename = path.split('/').pop() || path;

  return (
    <div className="file-editor">
      <div className="file-editor-header">
        <button className="file-editor-back" onClick={onClose}>&larr; Back</button>
        <span className="file-editor-path" title={path}>{filename}</span>
        <div className="file-editor-actions">
          {saveStatus !== 'idle' && (
            <span className={`file-editor-status status-${saveStatus}`}>
              {statusLabels[saveStatus]}
            </span>
          )}
          <button
            className="file-editor-save"
            onClick={handleSave}
            disabled={!dirty && saveStatus !== 'error'}
          >
            Save
          </button>
        </div>
      </div>
      {error && <div className="workspace-error">{error}</div>}
      {content === null ? (
        <div className="file-editor-loading">Loading...</div>
      ) : (
        <div className="file-editor-cm" ref={editorRef} />
      )}
    </div>
  );
}
