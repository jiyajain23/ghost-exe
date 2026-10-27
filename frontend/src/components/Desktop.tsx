import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, choosePhoto, getFiles, getHealth, openFile, resumeRun, sendChat, startRun } from '../api/client';
import type { AppId, FileDocument, FileId, FileMetadata, PhotoChoice, RunResponse, RunState } from '../api/types';
import { Documents } from '../apps/Documents';
import { Helper, type Exchange } from '../apps/Helper';
import { Window } from './Window';

const SAVE_KEY = 'ghost.currentRunId';
const APPS: { id: AppId; title: string; short: string }[] = [
  { id: 'explorer', title: 'File Explorer', short: 'Files' },
  { id: 'helper', title: 'HELPER Chat', short: 'HELPER' },
  { id: 'mail', title: 'Mail / Log Viewer', short: 'Mail / Logs' },
];

export function Desktop() {
  const [snapshot, setSnapshot] = useState<RunState | null>(null);
  const [files, setFiles] = useState<FileMetadata[]>([]);
  const [documents, setDocuments] = useState<Partial<Record<AppId, FileDocument>>>({});
  const [messages, setMessages] = useState<Exchange[]>([]);
  const [windows, setWindows] = useState<AppId[]>(['helper', 'explorer']);
  const [pending, setPending] = useState('Connecting to archive…');
  const [error, setError] = useState('');
  const [stale, setStale] = useState(false);
  const [connected, setConnected] = useState(false);
  const [saveWarning, setSaveWarning] = useState('');
  const [reduced, setReduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const lock = useRef(false);
  const retry = useRef<null | (() => void)>(null);
  const launcherRefs = useRef<Partial<Record<AppId, HTMLButtonElement | null>>>({});
  const active = windows.at(-1);
  const busy = pending !== '';

  const focus = useCallback((id: AppId) => setWindows(current => current.at(-1) === id ? current : [...current.filter(w => w !== id), id]), []);
  function launch(id: AppId) {
    focus(id);
    requestAnimationFrame(() => document.getElementById(`${id}-title`)?.focus());
  }
  function close(id: AppId) {
    setWindows(current => current.filter(w => w !== id));
    launcherRefs.current[id]?.focus();
  }
  async function perform(label: string, operation: () => Promise<void>) {
    if (lock.current) return;
    lock.current = true; setPending(label); setError(''); retry.current = null;
    try { await operation(); setConnected(true); }
    catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The archive request failed.');
      setConnected(false);
      retry.current ??= () => { void perform(label, operation); };
    } finally { lock.current = false; setPending(''); }
  }
  function applyState(state: RunState) {
    setSnapshot(state);
    setFiles(current => current.filter(f => state.visible_file_ids.includes(f.id)).map(f => ({ ...f, unread: !state.opened_file_ids.includes(f.id) })));
  }
  async function loadRun(result: RunResponse) {
    setSnapshot(result.snapshot);
    setMessages([{ speaker: 'HELPER', text: result.greeting }]);
    setFiles(await getFiles(result.snapshot.run_id));
    setStale(false);
  }
  async function loadExisting(id: string) {
    try { await loadRun(await resumeRun(id)); }
    catch (reason) {
      if (reason instanceof ApiError && [404, 422].includes(reason.status)) {
        setSnapshot(null); setFiles([]); setDocuments({}); setStale(true);
      }
      throw reason;
    }
  }
  async function connect() {
    try { await getHealth(); }
    catch { throw new ApiError('Cannot reach the local archive. Start the backend on 127.0.0.1:8000, then retry.'); }
    const id = localStorage.getItem(SAVE_KEY);
    if (id) await loadExisting(id);
  }
  useEffect(() => { void perform('Connecting to archive…', connect); }, []);
  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(preference.matches);
    preference.addEventListener('change', update);
    return () => preference.removeEventListener('change', update);
  }, []);

  function begin() {
    void perform('Restoring workstation…', async () => {
      localStorage.getItem(SAVE_KEY);
      const result = await startRun();
      setSnapshot(result.snapshot);
      try { localStorage.setItem(SAVE_KEY, result.run_id); }
      catch { setSaveWarning('The browser could not save the investigation ID. Keep this tab open; refresh cannot resume it.'); }
      // Retrying a failed file listing must only resume, never create another run.
      try { await loadRun(result); }
      catch (reason) {
        retry.current = () => { void perform('Loading archive…', async () => loadExisting(result.run_id)); };
        throw reason;
      }
    });
  }
  function read(id: FileId, target: 'explorer' | 'mail') {
    void perform('Opening document…', async () => {
      if (!snapshot) return;
      const result = await openFile(snapshot.run_id, id);
      applyState(result.snapshot);
      setDocuments(current => ({ ...current, [target]: result.file }));
    });
  }
  function photo(choice: PhotoChoice) {
    void perform('Recording photo choice…', async () => {
      if (!snapshot) return;
      const result = await choosePhoto(snapshot.run_id, choice);
      applyState(result.snapshot);
      setDocuments(current => Object.fromEntries(Object.entries(current).map(([app, doc]) => [app,
        doc.actions.length ? { ...doc, description: result.description } : doc])));
    });
  }
  function chat(message: string, done: () => void) {
    void perform('Waiting for HELPER…', async () => {
      if (!snapshot) return;
      const result = await sendChat(snapshot.run_id, message);
      applyState(result.snapshot);
      setMessages(current => [...current, { speaker: 'YOU', text: message }, { speaker: 'HELPER', text: result.reply }]);
      done();
    });
  }

  return <main className={`desktop ${reduced ? 'reduce-motion' : ''}`}>
    <header className="desktop-header"><span>BRIAR ANNEX <span className="header-divider">/</span> RECOVERED WORKSTATION</span><span>LOCAL IMAGE · 2003</span></header>
    <div className="desktop-brand" aria-hidden="true"><div className="vesper-mark">v</div><strong>Vesper<span>OS</span></strong><small>ARCHIVE EDITION / 2003</small><p>Everything, where you left it.</p></div>
    <nav className="desktop-icons" aria-label="Desktop applications">
      {APPS.map(app => <button key={app.id} ref={element => { launcherRefs.current[app.id] = element; }} disabled={!snapshot}
        onClick={() => launch(app.id)} aria-label={`Open ${app.title}`}>
        <span className={`desktop-icon icon-${app.id}`} aria-hidden="true">{app.id === 'helper' ? ':)' : app.id === 'mail' ? '✉' : ''}</span><span>{app.title}</span>
      </button>)}
    </nav>
    {!snapshot && <section className="boot-panel" aria-labelledby="boot-title">
      <div className="titlebar"><h1 id="boot-title">GHOST.EXE / Recovered image</h1></div>
      <div className="boot-content"><p className="eyebrow">ARCHIVE RESTORATION UTILITY</p><h2>A workstation left running.</h2>
        <p>Explore a fictional recovered desktop. Read its documents, examine the evidence, and speak to its resident assistant.</p>
        <p className="boot-note">Only virtual game files are available. Nothing here accesses your personal files.</p>
        <button disabled={busy || (!connected && !stale)} onClick={begin}>{stale ? 'Start new investigation' : 'Begin investigation'}</button>
        <p className="development-note">Phase 1 preview · opening archive only. The complete investigation comes later.</p>
      </div>
    </section>}
    {snapshot && <div className="workspace" aria-label="Application windows">
      {APPS.filter(app => windows.includes(app.id)).map(app => <Window key={app.id} id={app.id} title={app.title}
        active={active === app.id} order={windows.indexOf(app.id)} onFocus={() => focus(app.id)} onClose={() => close(app.id)}>
        {app.id === 'helper' ? <Helper messages={messages} busy={busy} sending={pending === 'Waiting for HELPER…'} onSend={chat} />
          : <Documents mode={app.id} files={files} document={documents[app.id]} snapshot={snapshot} busy={busy}
            onOpen={id => read(id, app.id as 'explorer' | 'mail')} onPhoto={photo} />}
      </Window>)}
      {windows.length === 0 && <p className="all-closed">Your investigation is still open. Choose an application on the desktop.</p>}
    </div>}
    <aside className="archive-status" aria-label="Archive status">
      <span>{snapshot ? `Investigation ${String(snapshot.run_index).padStart(3, '0')} · ${snapshot.opened_file_ids.length} / ${files.length} documents read` : 'No investigation loaded'}</span>
      <label><input type="checkbox" checked={reduced} onChange={event => setReduced(event.target.checked)} /> Reduced motion</label>
      <small>Phase 1 · mock dialogue · progression continues in Phase 2</small>
    </aside>
    <div className="notifications" aria-live="polite">
      {pending && <p className="pending" role="status">{pending}</p>}
      {error && <div className="error-panel" role="alert"><strong>Archive connection</strong><p>{error}</p>
        <button disabled={busy} onClick={() => retry.current?.()}>Retry request</button>
        {snapshot && <button disabled={busy} onClick={() => { void perform('Reloading investigation…', async () => {
          await loadExisting(snapshot.run_id); setDocuments({});
        }); }}>Reload investigation</button>}
      </div>}
      {saveWarning && <p className="error-panel">{saveWarning}</p>}
    </div>
    <footer className="taskbar"><span className="taskbar-brand">v <strong>Vesper</strong></span>
      <nav aria-label="Switch application">{APPS.filter(app => windows.includes(app.id) && snapshot).map(app => <button
        key={app.id} aria-pressed={active === app.id} onClick={() => launch(app.id)}><span className={`mini-icon icon-${app.id}`} aria-hidden="true" />{app.short}</button>)}</nav>
      <div className="clock" aria-label="Frozen image clock: October 31, 2003, 23:17"><span className={`connection-dot ${connected ? 'online' : ''}`} title={connected ? 'Local archive connected' : 'Local archive unavailable'} /><time>23:17<small>10/31/2003</small></time></div>
    </footer>
  </main>;
}
