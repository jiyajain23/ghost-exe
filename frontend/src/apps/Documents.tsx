import { useState } from 'react';
import type { FileDocument, FileId, FileMetadata, PhotoChoice, RunState } from '../api/types';
export function Documents({ mode, files, document, snapshot, busy, onOpen, onPhoto }: {
  mode: 'explorer' | 'mail'; files: FileMetadata[]; document?: FileDocument;
  snapshot: RunState; busy: boolean; onOpen: (id: FileId) => void; onPhoto: (choice: PhotoChoice) => void;
}) {
  const [folder, setFolder] = useState(mode === 'mail' ? 'Inbox' : 'All files');
  const available = files.filter(f => mode === 'explorer' ? f.app === 'explorer' : f.app === 'mail' || f.path.startsWith('/LOGS/'));
  const folders = mode === 'explorer' ? ['All files', ...new Set(available.map(f => f.path.split('/')[1]))] : ['Inbox', 'Drafts', 'Logs'];
  const visible = available.filter(f => mode === 'explorer' ? folder === 'All files' || f.path.split('/')[1] === folder
    : folder === 'Logs' ? f.path.startsWith('/LOGS/') : folder === 'Drafts' ? f.path.includes('/DRAFT') : f.app === 'mail' && !f.path.includes('/DRAFT'));
  return <>
    <div className="window-toolbar"><span>{mode === 'mail' ? 'Archived correspondence & logs' : 'Recovered workstation image'}</span><span className="readonly">Read only</span></div>
    <div className="addressbar"><span>Location</span><span className="address">{mode === 'mail' ? 'MAIL / ' : 'ADA-MERCER-03 / '}{folder}</span></div>
    <div className="document-layout"><nav className="folder-list" aria-label={`${mode} folders`}>
      {folders.map(name => <button key={name} aria-pressed={folder === name} onClick={() => setFolder(name)}><span className="folder-glyph" aria-hidden="true" />{name}</button>)}
    </nav><div className="document-main"><div className="file-list" aria-label="Available documents">
      <div className="file-list-heading"><span>Name</span><span>State</span></div>
      {visible.map(file => <button key={file.id} disabled={busy} className={`file-row ${document?.id === file.id ? 'selected' : ''}`}
        aria-label={`Open ${file.title}`} onClick={() => onOpen(file.id)}>
        <span><span className="paper-glyph" aria-hidden="true" />{file.title}</span><small>{file.unread ? 'Unread' : 'Read'}</small></button>)}
      {!visible.length && <p className="empty-list">No recovered items in this folder.</p>}
    </div><article className="document-preview" tabIndex={0} aria-label={document ? `Document ${document.title}` : 'Document preview'}>
      {document ? <><div className="document-heading"><strong>{document.title}</strong><span>{document.path}</span></div><pre>{document.content}</pre>
        {document.actions.length > 0 && <div className="photo-actions"><p>Choose once for this investigation.</p>
          <div className="button-row">{document.actions.map(choice => <button key={choice} disabled={busy || snapshot.photo_choice !== null} onClick={() => onPhoto(choice)}>
            {choice === 'inspect' ? 'Inspect negative' : 'Leave sealed'}</button>)}</div>
          {snapshot.photo_choice && <p className="saved-choice">Recorded: {snapshot.photo_choice === 'inspect' ? 'Inspect negative' : 'Leave sealed'}</p>}
          {document.description && <p className="photo-description">{document.description}</p>}
        </div>}</> : <div className="preview-empty"><span className="large-paper" aria-hidden="true" /><h2>Select a document</h2><p>Open a recovered file to read its contents.</p></div>}
    </article></div></div><footer className="window-status"><span>{visible.length} item{visible.length !== 1 ? 's' : ''}</span><span>Virtual archive · no device files</span></footer>
  </>;
}
