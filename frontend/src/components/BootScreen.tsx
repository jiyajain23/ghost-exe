import type { FC } from 'react';
import { RetroIcon } from './RetroIcons';

interface BootScreenProps {
  busy: boolean;
  connected: boolean;
  stale: boolean;
  error: string;
  pending: string;
  reduced: boolean;
  onBegin: () => void;
  onRetry?: () => void;
  onToggleReduced: (value: boolean) => void;
}

export const BootScreen: FC<BootScreenProps> = ({
  busy,
  connected,
  stale,
  error,
  pending,
  reduced,
  onBegin,
  onRetry,
  onToggleReduced,
}) => {
  return (
    <div
      className={`relative min-h-screen w-screen bg-[#111416] text-[#e1e2e5] font-sans select-none overflow-y-auto flex flex-col justify-between ${
        reduced ? 'reduce-motion' : ''
      }`}
    >
      {/* Subtle CRT Overlay */}
      <div className="fixed inset-0 crt-overlay pointer-events-none z-30 opacity-40" />

      {/* TOP HEADER: Clean Retro OS Strip */}
      <header className="relative z-40 flex justify-between items-center w-full px-4 py-2 bg-[#1e2327] border-b border-[#374151]">
        <div className="flex items-center gap-2.5">
          <RetroIcon name="terminal" size={18} className="text-[#008080]" />
          <span className="font-bold text-sm tracking-wide text-white font-mono">
            VESPER-OS // GHOST.EXE
          </span>
          <span className="text-xs px-2 py-0.5 bg-[#111416] border border-[#4b5563] text-[#76d6d5] font-mono font-bold">
            REV 4.51PG
          </span>
        </div>

        <div className="flex items-center gap-3 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span
              className={`inline-block w-2.5 h-2.5 rounded-full ${
                connected ? 'bg-[#22c55e]' : 'bg-[#ef4444] animate-pulse'
              }`}
            />
            <span className={connected ? 'text-[#86efac]' : 'text-[#fca5a5]'}>
              {connected ? 'ARCHIVE ONLINE' : 'ARCHIVE DISCONNECTED'}
            </span>
          </div>
          <span className="text-[#6b7280]">|</span>
          <span className="text-[#9ca3af]">PORT 8000</span>
        </div>
      </header>

      {/* MAIN CONTAINER: Centered, High-Legibility Investigation Card */}
      <main className="relative z-40 flex-1 flex flex-col items-center justify-center p-4 md:p-8 max-w-3xl mx-auto w-full">
        {/* Central Terminal Window Box */}
        <div className="w-full bg-[#1f2428] border-2 border-[#374151] shadow-2xl overflow-hidden rounded-sm">
          {/* Window Titlebar */}
          <div className="px-3 py-1.5 bg-gradient-to-r from-[#000080] via-[#006565] to-[#1084d0] text-white flex items-center justify-between">
            <div className="flex items-center gap-2">
              <RetroIcon name="skull" size={15} className="text-[#76d6d5]" />
              <span className="font-bold text-xs tracking-wider font-mono">
                WORKSTATION ARCHIVE RESTORATION UTILITY
              </span>
            </div>
            <span className="text-[11px] font-mono text-[#e3fffe]">
              IMAGE: BRIAR-ANNEX-2003
            </span>
          </div>

          <div className="p-6 md:p-8 space-y-6">
            {/* Header Title & Subtitle */}
            <div className="space-y-2 border-b border-[#374151] pb-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <span className="text-xs font-mono text-[#76d6d5] font-bold tracking-widest uppercase">
                  VESPER RESEARCH SUB-BASE 09 // TERMINAL 03
                </span>
                <span className="text-xs font-mono text-[#facc15] bg-[#854d0e]/30 px-2 py-0.5 rounded border border-[#854d0e]">
                  ANOMALOUS SESSION RECOVERED
                </span>
              </div>
              <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
                A workstation left running.
              </h1>
              <p className="text-sm md:text-base text-[#d1d5db] leading-relaxed">
                Step into a recovered 2003 desktop. Read its archived incident logs, inspect classified
                evidence, and cross-examine its resident indexing assistant, HELPER.
              </p>
            </div>

            {/* Hardware & Archive Telemetry Highlights */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 bg-[#111416] border border-[#374151] rounded-sm space-y-1">
                <div className="text-[#9ca3af]">RECORDED TIMESTAMP:</div>
                <div className="text-white font-bold text-sm">October 31, 2003 · 23:17:00</div>
              </div>
              <div className="p-3 bg-[#111416] border border-[#374151] rounded-sm space-y-1">
                <div className="text-[#9ca3af]">PRIMARY EVIDENCE:</div>
                <div className="text-[#76d6d5] font-bold text-sm">Sector 04 Latch &amp; Door B Contradiction</div>
              </div>
              <div className="p-3 bg-[#111416] border border-[#374151] rounded-sm space-y-1">
                <div className="text-[#9ca3af]">ACTIVE DAEMON:</div>
                <div className="text-[#86efac] font-bold text-sm">HELPER.EXE (Volatile Cache)</div>
              </div>
              <div className="p-3 bg-[#111416] border border-[#374151] rounded-sm space-y-1">
                <div className="text-[#9ca3af]">VIRTUAL SANDBOX:</div>
                <div className="text-white font-bold text-sm">Strictly Virtual · No Device Access</div>
              </div>
            </div>

            {/* Error Notification if Archive Backend is unreachable */}
            {error && (
              <div className="p-4 bg-[#3b1212] border-2 border-[#ef4444] rounded-sm text-xs space-y-2">
                <div className="flex items-center gap-2 font-bold text-[#fca5a5] text-sm">
                  <RetroIcon name="warning" size={16} />
                  <span>Cannot Reach Local Archive Server</span>
                </div>
                <p className="text-[#fecaca] leading-relaxed">{error}</p>
                {onRetry && (
                  <button
                    type="button"
                    onClick={onRetry}
                    disabled={busy}
                    className="px-4 py-1.5 bg-[#1f2428] border border-[#fca5a5] text-[#fca5a5] font-bold hover:bg-[#374151] transition-colors cursor-pointer"
                  >
                    Retry Connection (127.0.0.1:8000)
                  </button>
                )}
              </div>
            )}

            {/* Primary Action Button - Prominent, Large, High Contrast */}
            <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-xs text-[#9ca3af] font-mono">
                {stale
                  ? 'Previous run expired or not found on server.'
                  : 'Ready to mount desktop filesystem.'}
              </div>

              <button
                type="button"
                onClick={onBegin}
                disabled={busy || (!connected && !stale)}
                className="w-full sm:w-auto px-8 py-3.5 bg-[#008080] hover:bg-[#006565] active:bg-[#004f4f] text-white font-bold text-sm md:text-base uppercase tracking-wider border-2 border-[#76d6d5] shadow-xl transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 rounded-sm"
              >
                <RetroIcon name="play" size={16} fill="#ffffff" />
                <span>
                  {pending
                    ? pending
                    : stale
                    ? 'Start New Investigation'
                    : 'Begin Investigation'}
                </span>
              </button>
            </div>
          </div>

          {/* Footer Bar inside window */}
          <div className="px-4 py-2.5 bg-[#171b1e] border-t border-[#374151] flex flex-wrap items-center justify-between gap-3 text-xs text-[#9ca3af]">
            <label className="flex items-center gap-2 cursor-pointer hover:text-white">
              <input
                type="checkbox"
                checked={reduced}
                onChange={(e) => onToggleReduced(e.target.checked)}
                className="accent-[#008080] w-4 h-4 cursor-pointer"
              />
              <span>Reduced motion mode</span>
            </label>

            <span className="font-mono text-[11px]">
              Phase 1/2 · Briar Annex Offline Mystery Sandbox
            </span>
          </div>
        </div>
      </main>

      {/* FOOTER: Hardware Specs / Subtle Retro Strip */}
      <footer className="relative z-40 bg-[#1e2327] border-t border-[#374151] px-4 py-2 flex flex-wrap justify-between items-center text-xs text-[#9ca3af] font-mono gap-2">
        <span>BOARD: VSP-486DX4 // 640KB BASE OK // 16MB EXT OK</span>
        <span>COPYRIGHT (C) 1984-2003 VESPER SYSTEMS INC.</span>
      </footer>
    </div>
  );
};
