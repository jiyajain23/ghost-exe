import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ApiError,
  choosePhoto,
  contain,
  getFiles,
  getHealth,
  openFile,
  resumeRun,
  sendChat,
  startRun,
} from '../api/client';
import type {
  AppId,
  FileDocument,
  FileId,
  FileMetadata,
  PhotoChoice,
  RunResponse,
  RunState,
} from '../api/types';
import { Documents } from '../apps/Documents';
import { Helper, type Exchange } from '../apps/Helper';
import { Window } from './Window';
import { BootScreen } from './BootScreen';
import { TopNavBar } from './TopNavBar';
import { StartMenu } from './StartMenu';
import { SettingsModal } from './SettingsModal';
import { RetroIcon } from './RetroIcons';

const SAVE_KEY = 'ghost.currentRunId';

const APPS: { id: AppId; title: string; short: string; icon: 'folder' | 'skull' | 'mail' }[] = [
  { id: 'helper', title: 'GHOST.EXE (HELPER)', short: 'GHOST.EXE', icon: 'skull' },
  { id: 'explorer', title: 'File Explorer', short: 'Explorer', icon: 'folder' },
  { id: 'mail', title: 'Mail / Log Viewer', short: 'Mail / Logs', icon: 'mail' },
];

export function Desktop() {
  const [snapshot, setSnapshot] = useState<RunState | null>(null);
  const [files, setFiles] = useState<FileMetadata[]>([]);
  const [documents, setDocuments] = useState<Partial<Record<AppId, FileDocument>>>({});
  const [messages, setMessages] = useState<Exchange[]>([]);
  const [windows, setWindows] = useState<AppId[]>(['helper', 'explorer']);
  const [pending, setPending] = useState('Connecting to archive…');
  const [error, setError] = useState('');
  const [sending, setSending] = useState(false);
  const [helperStatus, setHelperStatus] = useState('Scripted dialogue ready');
  const chatLock = useRef(false);
  const generation = useRef(0);
  const [stale, setStale] = useState(false);
  const [connected, setConnected] = useState(false);
  const [saveWarning, setSaveWarning] = useState('');
  const [reduced, setReduced] = useState(() =>
    typeof window !== 'undefined'
      ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
      : false
  );
  const [scanlines, setScanlines] = useState(false); // default off for sharp, clear readability
  const [startMenuOpen, setStartMenuOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [selectedIcon, setSelectedIcon] = useState<string | null>('helper');

  const lock = useRef(false);
  const retry = useRef<null | (() => void)>(null);
  const launcherRefs = useRef<Partial<Record<AppId, HTMLButtonElement | null>>>({});
  const active = windows.at(-1);
  const busy = pending !== '';

  const focus = useCallback(
    (id: AppId) =>
      setWindows((current) =>
        current.at(-1) === id ? current : [...current.filter((w) => w !== id), id]
      ),
    []
  );

  function launch(id: AppId) {
    focus(id);
    requestAnimationFrame(() => document.getElementById(`${id}-title`)?.focus());
  }

  function close(id: AppId) {
    setWindows((current) => current.filter((w) => w !== id));
    launcherRefs.current[id]?.focus();
  }

  async function perform(label: string, operation: () => Promise<void>) {
    if (lock.current) return;
    lock.current = true;
    setPending(label);
    setError('');
    retry.current = null;
    try {
      await operation();
      setConnected(true);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The archive request failed.');
      setConnected(false);
      retry.current ??= () => {
        void perform(label, operation);
      };
    } finally {
      lock.current = false;
      setPending('');
    }
  }

  function applyState(state: RunState) {
    setSnapshot(state);
    setFiles((current) =>
      current
        .filter((f) => state.visible_file_ids.includes(f.id))
        .map((f) => ({ ...f, unread: !state.opened_file_ids.includes(f.id) }))
    );
  }

  async function loadRun(result: RunResponse) {
    setSnapshot(result.snapshot);
    setMessages([{ speaker: 'HELPER', text: result.greeting }]);
    setFiles(await getFiles(result.snapshot.run_id));
    setStale(false);
  }

  async function loadExisting(id: string) {
    try {
      await loadRun(await resumeRun(id));
    } catch (reason) {
      if (reason instanceof ApiError && [404, 422].includes(reason.status)) {
        setSnapshot(null);
        setFiles([]);
        setDocuments({});
        setStale(true);
      }
      throw reason;
    }
  }

  async function connect() {
    try {
      const health = await getHealth();
      setHelperStatus(health.agent_mode === 'ollama' ? 'Local Gemma dialogue configured' : 'Scripted dialogue ready');
    } catch {
      throw new ApiError(
        'Cannot reach the local archive. Start the backend on 127.0.0.1:8000, then retry.'
      );
    }
    const id = localStorage.getItem(SAVE_KEY);
    if (id) await loadExisting(id);
  }

  useEffect(() => {
    void perform('Connecting to archive…', connect);
  }, []);

  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(preference.matches);
    preference.addEventListener('change', update);
    return () => preference.removeEventListener('change', update);
  }, []);

  function begin() {
    void perform('Restoring workstation…', async () => {
      const result = await startRun();
      setSnapshot(result.snapshot);
      try {
        localStorage.setItem(SAVE_KEY, result.run_id);
      } catch {
        setSaveWarning(
          'The browser could not save the investigation ID. Keep this tab open; refresh cannot resume it.'
        );
      }
      try {
        await loadRun(result);
      } catch (reason) {
        retry.current = () => {
          void perform('Loading archive…', async () => loadExisting(result.run_id));
        };
        throw reason;
      }
    });
  }

  function restart() {
    generation.current += 1;
    localStorage.removeItem(SAVE_KEY);
    setSnapshot(null);
    setFiles([]);
    setDocuments({});
    setMessages([]);
    begin();
  }

  function read(id: FileId, target: 'explorer' | 'mail') {
    void perform('Opening document…', async () => {
      if (!snapshot) return;
      const result = await openFile(snapshot.run_id, id);
      applyState(result.snapshot);
      setFiles(await getFiles(result.snapshot.run_id));
      setDocuments((current) => ({ ...current, [target]: result.file }));
    });
  }

  function photo(choice: PhotoChoice) {
    void perform('Recording photo choice…', async () => {
      if (!snapshot) return;
      const result = await choosePhoto(snapshot.run_id, choice);
      applyState(result.snapshot);
      setDocuments((current) =>
        Object.fromEntries(
          Object.entries(current).map(([app, doc]) => [
            app,
            doc && doc.actions.length ? { ...doc, description: result.description } : doc,
          ])
        )
      );
    });
  }

  function chat(message: string, done: () => void) {
    if (!snapshot || chatLock.current || busy) return;
    chatLock.current = true;
    setSending(true);
    const runId = snapshot.run_id;
    const requestGeneration = generation.current;
    void (async () => {
      try {
        const result = await sendChat(runId, message);
        // Fetch fresh state: documents may have been opened during inference.
        const current = await resumeRun(runId);
        if (requestGeneration !== generation.current) return;
        applyState(current.snapshot);
        setHelperStatus(result.fallback
          ? 'HELPER connection interrupted or reply rejected. Scripted dialogue active; you can continue.'
          : 'HELPER ready');
        setMessages(entries => [...entries,
          { speaker: 'YOU', text: message }, { speaker: 'HELPER', text: result.reply },
          ...result.effects.filter(e => e.type === 'plant_clue' && e.hint)
            .map(e => ({ speaker: 'HELPER' as const, text: e.hint! })),
        ]);
        done();
      } catch (reason) {
        if (requestGeneration !== generation.current) return;
        setHelperStatus(reason instanceof Error ? reason.message : 'HELPER interrupted. Retry your message.');
      } finally {
        chatLock.current = false;
        setSending(false);
      }
    })();
  }

  // If no investigation is loaded, show the clean, legible Boot Screen
  if (!snapshot) {
    return (
      <BootScreen
        busy={busy}
        connected={connected}
        stale={stale}
        error={error}
        pending={pending}
        reduced={reduced}
        onBegin={begin}
        onRetry={() => {
          void perform('Connecting to archive…', connect);
        }}
        onToggleReduced={setReduced}
      />
    );
  }

  return (
    <div
      className={`relative h-screen w-screen overflow-hidden flex flex-col select-none bg-[#008080] ${
        reduced ? 'reduce-motion' : ''
      }`}
    >
      {/* Optional Subtle CRT Scanline Filter */}
      {scanlines && <div className="crt-overlay fixed inset-0 pointer-events-none z-30" />}

      {/* Classic Windows 98 Teal Desktop Wallpaper with Cursed Spectral Horror Artifact */}
      <div className="absolute inset-0 bg-[#008080] z-0 overflow-hidden pointer-events-none">
        <div className="ghost-artifact absolute inset-0 flex items-center justify-center select-none mix-blend-color-burn opacity-20">
          <div className="relative w-[500px] h-[540px] flex flex-col items-center justify-center">
            <div className="w-64 h-72 rounded-full bg-gradient-to-t from-transparent via-[#004f4f]/20 to-[#002020]/50 blur-3xl transform -translate-y-10" />
            <div className="absolute top-28 flex gap-16">
              <div className="w-5 h-7 bg-[#1a1c1c] rounded-full blur-sm opacity-60" />
              <div className="w-4 h-6 bg-[#1a1c1c] rounded-full blur-sm opacity-50" />
            </div>
            <div className="w-96 h-96 bg-black/30 blur-3xl absolute -bottom-10" />
            <div className="font-mono text-xl text-[#002020]/30 tracking-[0.4em] uppercase select-none mt-4 font-bold">
              I CAN SEE YOU
            </div>
          </div>
        </div>
      </div>

      {/* Top Application Menu & OS Strip with CRT toggle */}
      <TopNavBar
        scanlines={scanlines}
        onToggleScanlines={() => setScanlines(!scanlines)}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      {/* Main Desktop Workspace (Icons Canvas + Floating Windows) */}
      <main
        className="flex-1 w-full relative z-10 p-2 md:p-3 pb-10 overflow-hidden flex"
        onClick={() => {
          if (startMenuOpen) setStartMenuOpen(false);
        }}
      >
        {/* DESKTOP SHORTCUT ICONS */}
        <section
          aria-label="Desktop Shortcut Icons"
          className="flex flex-col gap-4 w-24 md:w-28 shrink-0 z-20 self-start pt-3"
        >
          {/* Icon 1: GHOST.EXE */}
          <div
            tabIndex={0}
            role="button"
            aria-label="Launch GHOST.EXE"
            onClick={() => {
              setSelectedIcon('helper');
              launch('helper');
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') launch('helper');
            }}
            className={`group flex flex-col items-center p-1.5 cursor-pointer focus:outline-none rounded-xs transition-colors ${
              selectedIcon === 'helper' ? 'dotted-focus bg-white/10' : 'hover:bg-white/10'
            }`}
          >
            <div className="w-12 h-12 bg-[#fee2e2] border-2 border-[#b91c1c] flex items-center justify-center relative shadow-md rounded-xs">
              <RetroIcon name="skull" size={28} className="text-[#b91c1c]" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-[#b91c1c]" />
            </div>
            <span className="mt-1.5 text-xs font-mono text-center text-white bg-[#b91c1c] px-1.5 py-0.5 leading-tight font-bold rounded-xs">
              GHOST.EXE
            </span>
          </div>

          {/* Icon 2: File Explorer */}
          <div
            tabIndex={0}
            role="button"
            aria-label="Open File Explorer"
            onClick={() => {
              setSelectedIcon('explorer');
              launch('explorer');
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') launch('explorer');
            }}
            className={`group flex flex-col items-center p-1.5 cursor-pointer rounded-xs transition-colors focus:outline-none ${
              selectedIcon === 'explorer' ? 'dotted-focus bg-white/10' : 'hover:bg-white/10'
            }`}
          >
            <div className="w-12 h-12 bg-[#c0c0c0] w98-bevel-raised flex items-center justify-center rounded-xs shadow-md">
              <RetroIcon name="folder" size={28} />
            </div>
            <span className="mt-1.5 text-xs text-center text-white drop-shadow-[0_1px_2px_rgba(0,0,0,1)] px-1 leading-tight font-bold">
              Archives
            </span>
          </div>

          {/* Icon 3: Mail / Logs */}
          <div
            tabIndex={0}
            role="button"
            aria-label="Open Mail Viewer"
            onClick={() => {
              setSelectedIcon('mail');
              launch('mail');
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') launch('mail');
            }}
            className={`group flex flex-col items-center p-1.5 cursor-pointer rounded-xs transition-colors focus:outline-none ${
              selectedIcon === 'mail' ? 'dotted-focus bg-white/10' : 'hover:bg-white/10'
            }`}
          >
            <div className="w-12 h-12 bg-[#c0c0c0] w98-bevel-raised flex items-center justify-center rounded-xs shadow-md">
              <RetroIcon name="mail" size={28} />
            </div>
            <span className="mt-1.5 text-xs text-center text-white drop-shadow-[0_1px_2px_rgba(0,0,0,1)] px-1 leading-tight font-bold">
              Mail Viewer
            </span>
          </div>

          {/* Icon 4: System Settings */}
          <div
            tabIndex={0}
            role="button"
            aria-label="Open System Properties"
            onClick={() => {
              setSelectedIcon('settings');
              setSettingsOpen(true);
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') setSettingsOpen(true);
            }}
            className={`group flex flex-col items-center p-1.5 cursor-pointer rounded-xs transition-colors focus:outline-none ${
              selectedIcon === 'settings' ? 'dotted-focus bg-white/10' : 'hover:bg-white/10'
            }`}
          >
            <div className="w-12 h-12 bg-[#c0c0c0] w98-bevel-raised flex items-center justify-center rounded-xs shadow-md">
              <RetroIcon name="settings" size={28} />
            </div>
            <span className="mt-1.5 text-xs text-center text-white drop-shadow-[0_1px_2px_rgba(0,0,0,1)] px-1 leading-tight font-bold">
              Settings
            </span>
          </div>
        </section>

        {/* APPLICATION WINDOWS CANVAS */}
        <div className="flex-1 relative h-full ml-1 md:ml-3">
          {APPS.filter((app) => windows.includes(app.id)).map((app) => (
            <Window
              key={app.id}
              id={app.id}
              title={app.title}
              active={active === app.id}
              order={windows.indexOf(app.id)}
              onFocus={() => focus(app.id)}
              onClose={() => close(app.id)}
            >
              {app.id === 'helper' ? (
                <Helper
                  messages={messages}
                  busy={busy}
                  sending={sending}
                  status={helperStatus}
                  runIndex={snapshot.run_index}
                  onSend={chat}
                />
              ) : (
                <Documents
                  mode={app.id}
                  files={files}
                  document={documents[app.id]}
                  snapshot={snapshot}
                  busy={busy}
                  onOpen={(id) => read(id, app.id as 'explorer' | 'mail')}
                  onPhoto={photo}
                  onContain={(step) => void perform('Containment…', async () => {
                    const result = await contain(snapshot.run_id, step);
                    applyState(result.snapshot);
                    setMessages(entries => [...entries, { speaker: 'HELPER', text: result.message }]);
                  })}
                />
              )}
            </Window>
          ))}

          {windows.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center text-white p-6">
              <div className="p-6 bg-[#c0c0c0] w98-bevel-raised shadow-2xl max-w-md text-black space-y-4">
                <div className="flex items-center gap-2 justify-center font-bold text-sm text-[#006565]">
                  <RetroIcon name="computer" size={22} />
                  <span>Investigation Session Active</span>
                </div>
                <p className="text-xs text-[#374151] leading-relaxed">
                  All application windows are currently closed. Choose an application below to continue:
                </p>
                <div className="flex flex-col sm:flex-row gap-2 justify-center">
                  <button
                    type="button"
                    onClick={() => launch('helper')}
                    className="px-3 py-1.5 w98-btn font-bold text-xs text-[#006565]"
                  >
                    Open HELPER Chat
                  </button>
                  <button
                    type="button"
                    onClick={() => launch('explorer')}
                    className="px-3 py-1.5 w98-btn font-bold text-xs"
                  >
                    Open File Explorer
                  </button>
                  <button
                    type="button"
                    onClick={() => launch('mail')}
                    className="px-3 py-1.5 w98-btn font-bold text-xs"
                  >
                    Open Mail Viewer
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Start Menu Popup */}
      <StartMenu
        isOpen={startMenuOpen}
        onClose={() => setStartMenuOpen(false)}
        onLaunch={launch}
        onOpenSettings={() => setSettingsOpen(true)}
        onRestartInvestigation={restart}
      />

      {/* Settings Modal */}
      {settingsOpen && (
        <SettingsModal
          snapshot={snapshot}
          reduced={reduced}
          scanlines={scanlines}
          onToggleReduced={setReduced}
          onToggleScanlines={setScanlines}
          onClose={() => setSettingsOpen(false)}
          onReload={() => {
            void perform('Reloading investigation…', async () => {
              await loadExisting(snapshot.run_id);
              setDocuments({});
              setSettingsOpen(false);
            });
          }}
          onRestart={() => {
            setSettingsOpen(false);
            restart();
          }}
        />
      )}

      {/* Notifications / Error Dialog */}
      {(error || pending || saveWarning) && (
        <div className="fixed bottom-11 right-3 z-50 max-w-sm w-full bg-[#c0c0c0] w98-bevel-raised shadow-2xl p-2.5 font-sans text-xs">
          <div className="h-6 px-2 py-0.5 bg-gradient-to-r from-[#b91c1c] to-[#7f1d1d] text-white font-bold text-xs flex items-center justify-between mb-2">
            <span>{error ? 'System Alert' : pending ? 'Archive Status' : 'Notice'}</span>
            <button
              type="button"
              onClick={() => {
                setError('');
                setSaveWarning('');
              }}
              className="text-white font-bold hover:text-black cursor-pointer px-1"
            >
              ×
            </button>
          </div>

          <div className="p-2.5 w98-bevel-sunken bg-white text-black space-y-2">
            {pending && (
              <div className="flex items-center gap-2 text-[#006565] font-bold">
                <span className="w-2 h-2 rounded-full bg-[#008080] animate-ping" />
                <span>{pending}</span>
              </div>
            )}
            {error && <p className="text-[#b91c1c] font-medium leading-relaxed">{error}</p>}
            {saveWarning && <p className="text-[#374151] leading-relaxed">{saveWarning}</p>}
          </div>

          {error && retry.current && (
            <div className="pt-2 flex justify-end gap-2">
              <button
                type="button"
                disabled={busy}
                onClick={() => retry.current?.()}
                className="px-4 py-1 w98-btn text-xs font-bold"
              >
                Retry Request
              </button>
            </div>
          )}
        </div>
      )}

      {/* Bottom Retro Windows 98 Taskbar */}
      <footer className="fixed bottom-0 left-0 w-full z-40 flex justify-between items-center px-1.5 py-0.5 bg-[#c0c0c0] w98-bevel-raised text-xs select-none h-8 md:h-9">
        {/* Left: START Button & Running Tabs */}
        <div className="flex items-center gap-1.5 overflow-hidden">
          <button
            type="button"
            onClick={() => setStartMenuOpen(!startMenuOpen)}
            className={`bg-[#c0c0c0] text-black px-2.5 py-1 font-bold flex items-center gap-1.5 cursor-pointer text-xs ${
              startMenuOpen ? 'w98-bevel-sunken' : 'w98-bevel-raised'
            }`}
          >
            <span className="w-4 h-4 grid grid-cols-2 gap-0.5 shrink-0">
              <span className="bg-[#b91c1c]" />
              <span className="bg-[#15803d]" />
              <span className="bg-[#008080]" />
              <span className="bg-[#4338ca]" />
            </span>
            <span className="tracking-wide font-sans">Start</span>
          </button>

          <div className="h-5 w-px bg-[#808080] border-r border-white mx-1 hidden sm:block shrink-0" />

          {/* Running Program Tabs in Taskbar */}
          <div className="flex items-center gap-1.5 overflow-x-auto">
            {APPS.filter((app) => windows.includes(app.id)).map((app) => {
              const isActive = active === app.id;
              return (
                <button
                  key={app.id}
                  type="button"
                  onClick={() => launch(app.id)}
                  className={`px-3 py-1 text-xs flex items-center gap-2 cursor-pointer truncate max-w-[150px] md:max-w-[180px] rounded-xs ${
                    isActive
                      ? 'bg-[#ffffff] text-[#006565] font-bold w98-bevel-sunken'
                      : 'bg-[#c0c0c0] text-[#1a1c1c] w98-bevel-raised hover:bg-[#dfdfdf]'
                  }`}
                >
                  <RetroIcon name={app.icon} size={14} className="shrink-0" />
                  <span className="truncate">{app.short}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right: Windows 98 Sunken System Tray */}
        <div className="flex items-center gap-2 bg-[#c0c0c0] w98-bevel-sunken-sm px-2 py-0.5 text-xs shrink-0">
          <button
            type="button"
            title="System Settings"
            onClick={() => setSettingsOpen(true)}
            className="hover:opacity-80 cursor-pointer flex items-center"
          >
            <RetroIcon name="settings" size={14} />
          </button>

          <div className="h-4 w-px bg-[#808080] border-r border-white mx-0.5" />

          {/* Digital Clock stuck at 10/31/2003 23:17 */}
          <time
            className="font-mono text-xs text-[#1a1c1c] font-bold whitespace-nowrap pl-0.5 flex items-center gap-2"
            dateTime="2003-10-31T23:17"
            title="Frozen Archive Timestamp: 10/31/2003 23:17"
          >
            <span
              className={`w-2 h-2 rounded-full ${
                connected ? 'bg-[#15803d]' : 'bg-[#b91c1c]'
              }`}
              title={connected ? 'Archive online' : 'Archive offline'}
            />
            <span>23:17</span>
          </time>
        </div>
      </footer>
    </div>
  );
}
