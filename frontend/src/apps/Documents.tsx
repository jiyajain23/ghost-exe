import { useState, type FC } from 'react';
import type { FileDocument, FileId, FileMetadata, PhotoChoice, RunState } from '../api/types';
import { RetroIcon } from '../components/RetroIcons';

interface DocumentsProps {
  mode: 'explorer' | 'mail';
  files: FileMetadata[];
  document?: FileDocument;
  snapshot: RunState;
  busy: boolean;
  onOpen: (id: FileId) => void;
  onContain: (step: string) => void;
  onPhoto: (choice: PhotoChoice) => void;
}

function toHexDump(text: string): string {
  const lines: string[] = [];
  const bytes = new TextEncoder().encode(text);
  for (let i = 0; i < bytes.length; i += 16) {
    const chunk = bytes.slice(i, i + 16);
    const hex = Array.from(chunk)
      .map(b => b.toString(16).padStart(2, '0').toUpperCase())
      .join(' ')
      .padEnd(48, ' ');
    const ascii = Array.from(chunk)
      .map(b => (b >= 32 && b <= 126 ? String.fromCharCode(b) : '.'))
      .join('');
    const offset = i.toString(16).padStart(8, '0').toUpperCase();
    lines.push(`${offset}  ${hex}  |${ascii}|`);
  }
  return lines.join('\n');
}

export const Documents: FC<DocumentsProps> = ({
  mode,
  files,
  document,
  snapshot,
  busy,
  onOpen,
  onPhoto,
  onContain,
}) => {
  const [folder, setFolder] = useState(mode === 'mail' ? 'Inbox' : 'All files');
  const [hexMode, setHexMode] = useState(false);
  const [showRedactions, setShowRedactions] = useState(true);

  const available = files.filter(f =>
    mode === 'explorer' ? f.app === 'explorer' : f.app === 'mail' || f.path.startsWith('/LOGS/')
  );

  const folders = mode === 'explorer'
    ? ['All files', ...Array.from(new Set(available.map(f => f.path.split('/')[1])))]
    : ['Inbox', 'Drafts', 'Logs'];

  const visible = available.filter(f => {
    if (mode === 'explorer') {
      return folder === 'All files' || f.path.split('/')[1] === folder;
    }
    if (folder === 'Logs') return f.path.startsWith('/LOGS/');
    if (folder === 'Drafts') return f.path.includes('/DRAFT');
    return f.app === 'mail' && !f.path.includes('/DRAFT');
  });

  return (
    <div className="flex-1 flex flex-col h-full min-h-0 bg-[#c0c0c0] font-sans text-xs select-none">
      {/* Window Action Toolbar with Win98 3D Bevel Buttons */}
      <div className="flex flex-wrap items-center justify-between gap-1 p-1.5 bg-[#c0c0c0] border-b border-[#808080] shrink-0">
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => {
              if (document) {
                const blob = new Blob([document.content], { type: 'text/plain' });
                const url = URL.createObjectURL(blob);
                const a = window.document.createElement('a');
                a.href = url;
                a.download = `${document.id}_${document.title}.txt`;
                a.click();
                URL.revokeObjectURL(url);
              }
            }}
            disabled={!document}
            className="w98-btn px-2.5 py-1 text-xs active:bevel-inset hover:bg-[#dfdfdf] cursor-pointer disabled:opacity-50"
            title="Download copy of this file"
          >
            <RetroIcon name="document" size={14} />
            <span>Save Text</span>
          </button>

          <button
            type="button"
            onClick={() => window.print()}
            disabled={!document}
            className="w98-btn px-2.5 py-1 text-xs active:bevel-inset hover:bg-[#dfdfdf] cursor-pointer disabled:opacity-50"
            title="Print document"
          >
            <RetroIcon name="print" size={14} />
            <span>Print</span>
          </button>
        </div>

        {/* Investigation Cursed Mode Toggles */}
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => setShowRedactions(!showRedactions)}
            className={`w98-btn px-2.5 py-1 font-bold text-xs cursor-pointer ${
              showRedactions ? 'text-[#b91c1c] bg-[#fee2e2]' : 'text-[#1a1c1c]'
            }`}
          >
            <RetroIcon name="visibility-off" size={14} />
            <span>{showRedactions ? 'Redactions: Hidden' : 'Redactions: Revealed'}</span>
          </button>

          <button
            type="button"
            onClick={() => setHexMode(!hexMode)}
            disabled={!document}
            className={`w98-btn px-2.5 py-1 font-bold text-xs cursor-pointer disabled:opacity-50 ${
              hexMode ? 'bg-[#008080] text-white' : 'text-[#006565]'
            }`}
          >
            <RetroIcon name="data-array" size={14} />
            <span>{hexMode ? 'Text Mode' : 'Hex Dump'}</span>
          </button>
        </div>
      </div>

      {/* Address Bar */}
      <div className="px-3 py-1.5 bg-[#d4d0c8] border-b border-[#808080] flex items-center justify-between text-xs font-mono shrink-0">
        <div className="flex items-center gap-2 truncate">
          <span className="text-[#4b5563] font-sans font-bold">Location:</span>
          <span className="bg-white px-2 py-0.5 border border-[#808080] text-[#000080] truncate font-bold">
            {mode === 'mail' ? `C:\\VESPER\\MAIL\\${folder}` : `C:\\ARCHIVE\\ADA-MERCER-03\\${folder}`}
          </span>
        </div>
        <span className="text-[#006565] font-bold text-xs hidden sm:inline ml-2 whitespace-nowrap">
          {visible.length} Item(s)
        </span>
      </div>

      {/* Window Inner Workspace: Split Pane (Tree Explorer & Light Paper Document Canvas) */}
      <div className="flex-1 flex flex-col md:flex-row min-h-0 bg-[#d4d0c8] overflow-hidden">
        {/* LEFT ARCHIVE TREE / FOLDER & FILE PANE */}
        <aside className="w-full md:w-64 bg-white w98-bevel-sunken p-2.5 border-r border-[#808080] flex flex-col justify-between overflow-y-auto shrink-0 min-h-[180px] md:min-h-0">
          <div>
            {/* Folder Header */}
            <div className="flex items-center gap-1.5 text-xs font-bold text-[#006565] pb-1.5 border-b border-[#808080] mb-2 font-mono">
              <RetroIcon name="folder-special" size={15} />
              <span>{mode === 'mail' ? 'MAIL DIRECTORY' : 'DOCUMENT ARCHIVE'}</span>
            </div>

            {/* Folder Tabs */}
            <div className="flex flex-wrap gap-1 mb-3 font-sans">
              {folders.map(name => (
                <button
                  key={name}
                  type="button"
                  onClick={() => setFolder(name)}
                  className={`px-2.5 py-1 text-xs font-medium flex items-center gap-1.5 cursor-pointer rounded-xs ${
                    folder === name
                      ? 'bg-[#008080] text-white font-bold w98-bevel-sunken'
                      : 'bg-[#c0c0c0] text-[#1a1c1c] w98-bevel-raised hover:bg-[#dfdfdf]'
                  }`}
                >
                  <RetroIcon name={folder === name ? 'folder-open' : 'folder'} size={14} />
                  <span>{name}</span>
                </button>
              ))}
            </div>

            {/* Canonical File Items List */}
            <div className="space-y-1 font-sans text-xs">
              {visible.map(file => {
                const isSelected = document?.id === file.id;
                return (
                  <button
                    key={file.id}
                    disabled={busy}
                    onClick={() => onOpen(file.id)}
                    className={`w-full text-left p-1.5 flex items-center justify-between gap-1.5 rounded-xs border border-transparent cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-[#000080] text-white font-bold'
                        : 'hover:bg-[#f3f4f6] text-[#1f2937]'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <RetroIcon
                        name={file.app === 'mail' ? 'mail' : 'document'}
                        size={15}
                        className={isSelected ? 'text-white' : 'text-[#008080]'}
                      />
                      <span className="truncate text-xs">{file.title}</span>
                    </div>

                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded-xs uppercase font-bold shrink-0 font-mono ${
                        file.unread
                          ? 'bg-[#fee2e2] text-[#b91c1c]'
                          : isSelected
                          ? 'bg-white/20 text-white'
                          : 'bg-[#e5e7eb] text-[#6b7280]'
                      }`}
                    >
                      {file.unread ? 'NEW' : 'READ'}
                    </span>
                  </button>
                );
              })}

              {visible.length === 0 && (
                <div className="p-4 text-center text-[#6b7280] italic text-xs">
                  No files found in this folder.
                </div>
              )}
            </div>
          </div>

          {/* Mini-Status Box */}
          <div className="mt-3 p-2 bg-[#f9fafb] border border-[#d1d5db] font-mono text-[11px] shrink-0">
            <div className="text-[#006565] flex items-center justify-between font-bold">
              <span>STATUS:</span>
              <span className="text-[#15803d]">LOGGED</span>
            </div>
            <p className="text-[#6b7280] text-[10px] mt-0.5 leading-tight">
              Evidence access is monitored by the local director engine.
            </p>
          </div>
        </aside>

        {/* RIGHT DOCUMENT CONTENT CANVAS: High-Contrast, Spacious Reading */}
        <article
          tabIndex={0}
          aria-label={document ? `Document ${document.title}` : 'Document preview'}
          className="flex-1 bg-white w98-bevel-sunken p-4 md:p-6 overflow-y-auto flex flex-col justify-between font-mono text-xs focus:outline-none"
        >
          {document ? (
            <div className="space-y-4 leading-relaxed max-w-3xl">
              {/* Document Header */}
              <div className="border-b-2 border-[#008080]/30 pb-3 flex flex-col gap-1">
                <div className="font-bold text-base text-[#006565] tracking-wide font-sans">
                  {mode === 'mail'
                    ? 'VESPER INTERNAL CORRESPONDENCE DISCLOSURE'
                    : 'VESPER RESEARCH SUB-BASE 09 — INCIDENT RECORD'}
                </div>
                <div className="text-xs text-[#6b7280]">
                  DOCUMENT: <span className="font-bold text-[#000080]">{document.id}</span> //{' '}
                  PATH: <span className="font-bold text-[#1f2937]">{document.path}</span>
                </div>
              </div>

              {/* Metadata Block */}
              <div className="bg-[#f8fafc] p-3 border border-[#cbd5e1] text-xs grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-[#475569] font-sans">
                <div>DATE: <span className="text-black font-bold">October 31, 2003</span></div>
                <div>CLASSIFICATION: <span className="text-[#b91c1c] font-bold">ALPHA-RESTRICTED</span></div>
                <div>TITLE: <span className="text-black font-bold">{document.title}</span></div>
                <div>STATUS: <span className="text-[#008080] font-bold">VERIFIED RECOVERED</span></div>
              </div>

              {/* Document Text Body */}
              {hexMode ? (
                <div className="bg-[#0c0f11] text-emerald-400 p-3 border border-[#374151] overflow-x-auto text-xs leading-relaxed font-mono whitespace-pre rounded-sm">
                  {toHexDump(document.content)}
                </div>
              ) : (
                <div className="space-y-3 text-[#111827] text-sm leading-relaxed whitespace-pre-wrap break-words font-mono">
                  {document.content.split('\n\n').map((paragraph, pIdx) => {
                    const isHelperAnomaly =
                      paragraph.includes('HELPER:') ||
                      paragraph.includes('[HELPER') ||
                      paragraph.includes('DOOR B LOCKED');

                    if (isHelperAnomaly) {
                      return (
                        <div
                          key={pIdx}
                          className="p-3 border-l-4 border-[#ef4444] bg-[#fee2e2]/60 text-[#b91c1c] font-bold my-3 rounded-xs"
                        >
                          {paragraph}
                        </div>
                      );
                    }

                    if (showRedactions && paragraph.includes('██')) {
                      return (
                        <p key={pIdx}>
                          {paragraph.split(/(██+)/g).map((part, partIdx) =>
                            part.startsWith('█') ? (
                              <span
                                key={partIdx}
                                title="Hover to reveal redacted text"
                                className="redaction-bar"
                              >
                                {part}
                              </span>
                            ) : (
                              part
                            )
                          )}
                        </p>
                      );
                    }

                    return <p key={pIdx}>{paragraph}</p>;
                  })}
                </div>
              )}

              {document.id === 'F10' && snapshot.clues.includes('C4_CONTAINMENT_READY') && (
                <section aria-label="Containment Console" className="p-4 border-2 border-black">
                  <h3>Containment Console</h3>
                  {snapshot.status === 'completed' ? <p>{snapshot.ending}</p> :
                    ['ISOLATE', 'VERIFY', 'DISCONNECT'].map((step, index) => (
                      <button key={step} className="w98-btn p-2" disabled={busy || snapshot.status !== 'active' || snapshot.containment_index !== index}
                        onClick={() => onContain(step)}>{step}</button>
                    ))}
                </section>
              )}
              {/* F02 Photo Negative Choices */}
              {document.actions.length > 0 && (
                <div className="mt-6 p-4 bg-[#f8fafc] border-2 border-[#008080] space-y-3 font-sans rounded-xs shadow-sm">
                  <div className="font-bold text-sm text-[#006565] flex items-center gap-2">
                    <RetroIcon name="warning" size={16} className="text-[#b91c1c]" />
                    <span>INVESTIGATOR DECISION — PHOTO NEGATIVE RETENTION:</span>
                  </div>
                  <p className="text-xs text-[#4b5563] leading-relaxed">
                    Choose once for this investigation. Your decision is recorded and influences HELPER&#39;s recall in subsequent investigations.
                  </p>

                  <div className="flex flex-wrap gap-3 pt-1">
                    {document.actions.map(choice => (
                      <button
                        key={choice}
                        type="button"
                        disabled={busy || snapshot.photo_choice !== null}
                        onClick={() => onPhoto(choice)}
                        className={`px-4 py-2 w98-btn font-bold text-xs cursor-pointer ${
                          choice === 'inspect'
                            ? 'text-[#006565] hover:bg-[#e6fffa]'
                            : 'text-[#b91c1c] hover:bg-[#fee2e2]'
                        }`}
                      >
                        {choice === 'inspect' ? '[ INSPECT NEGATIVE ]' : '[ LEAVE SEALED ]'}
                      </button>
                    ))}
                  </div>

                  {snapshot.photo_choice && (
                    <div className="text-xs font-bold text-[#008080] pt-1">
                      Recorded Choice: {snapshot.photo_choice === 'inspect' ? 'INSPECT NEGATIVE' : 'LEAVE SEALED'}
                    </div>
                  )}

                  {document.description && (
                    <p className="p-3 bg-white border border-[#cbd5e1] text-xs text-[#111827] font-mono leading-relaxed mt-2 rounded-xs">
                      {document.description}
                    </p>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-[#6b7280]">
              <RetroIcon name="folder-open" size={54} className="text-[#9ca3af] mb-3" />
              <h2 className="font-bold text-base text-[#111827] mb-1 font-sans">
                Select a Document
              </h2>
              <p className="text-xs max-w-md font-sans">
                Choose a recovered artifact from the directory tree on the left to inspect its contents and cross-examine evidence.
              </p>
            </div>
          )}
        </article>
      </div>

      {/* Window Status Bar */}
      <footer className="h-6 bg-[#c0c0c0] px-3 border-t border-[#808080] flex items-center justify-between text-xs text-[#374151] select-none font-mono shrink-0">
        <div className="flex items-center gap-3">
          <span>{visible.length} ITEM(S) AVAILABLE</span>
          <span className="border-l border-[#808080] pl-3">ENCODING: UTF-8</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[#006565] font-bold">
            {document ? document.title : 'NO FILE SELECTED'}
          </span>
        </div>
      </footer>
    </div>
  );
};
