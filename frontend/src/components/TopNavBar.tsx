import type { FC } from 'react';
import type { RunState } from '../api/types';
import { RetroIcon } from './RetroIcons';

interface TopNavBarProps {
  scanlines: boolean;
  snapshot?: RunState | null;
  onToggleScanlines: () => void;
  onOpenSettings?: () => void;
}

export const TopNavBar: FC<TopNavBarProps> = ({
  scanlines,
  snapshot,
  onToggleScanlines,
  onOpenSettings,
}) => {
  const c1 = snapshot?.clues.includes('C1_ACCESS_CONTRADICTION');
  const c2 = snapshot?.clues.includes('C2_LOG_TAMPERING');
  const c3 = snapshot?.clues.includes('C3_LOCK_PROOF');
  const c4 = snapshot?.clues.includes('C4_CONTAINMENT_READY');
  const cluesCount = [c1, c2, c3, c4].filter(Boolean).length;

  return (
    <header className="flex justify-between items-center w-full px-3 py-1 bg-[#c0c0c0] border-b border-[#808080] z-20 relative w98-bevel-raised-sm select-none h-8 shrink-0">
      <div className="flex items-center gap-2.5">
        <RetroIcon name="bug-report" size={16} className="text-[#b91c1c]" />
        <h1 className="text-xs font-bold text-[#1a1c1c] uppercase tracking-wide font-sans">
          VESPER-OS // GHOST.EXE
        </h1>
        <span className="text-[11px] font-mono font-bold text-[#006565] bg-[#ffffff] px-2 py-0.2 border border-[#808080]">
          v4.1.0-RC3
        </span>
      </div>

      {/* Case Clue Tracker in Navigation Strip */}
      <div className="flex items-center gap-1.5 text-xs font-mono">
        <span className="text-[#404040] font-bold hidden sm:inline text-[11px]">
          CASE PROGRESS ({cluesCount}/4):
        </span>
        <div className="flex items-center gap-1">
          <span
            className={`px-1.5 py-0.2 border text-[11px] font-bold ${
              c1 ? 'bg-[#1e3a8a] text-white border-[#172554]' : 'bg-[#e5e7eb] text-[#9ca3af] border-[#d1d5db]'
            }`}
            title="C1: Access Contradiction (FAQ vs Eli's memo)"
          >
            C1 {c1 ? '✓' : '—'}
          </span>
          <span
            className={`px-1.5 py-0.2 border text-[11px] font-bold ${
              c2 ? 'bg-[#1e3a8a] text-white border-[#172554]' : 'bg-[#e5e7eb] text-[#9ca3af] border-[#d1d5db]'
            }`}
            title="C2: Log Tampering (Access log vs Recovered cache)"
          >
            C2 {c2 ? '✓' : '—'}
          </span>
          <span
            className={`px-1.5 py-0.2 border text-[11px] font-bold ${
              c3 ? 'bg-[#1e3a8a] text-white border-[#172554]' : 'bg-[#e5e7eb] text-[#9ca3af] border-[#d1d5db]'
            }`}
            title="C3: Lock Proof (Door B security trace)"
          >
            C3 {c3 ? '✓' : '—'}
          </span>
          <span
            className={`px-1.5 py-0.2 border text-[11px] font-bold ${
              c4 ? 'bg-[#831843] text-white border-[#500724]' : 'bg-[#e5e7eb] text-[#9ca3af] border-[#d1d5db]'
            }`}
            title="C4: Containment Ready (Maintenance protocol)"
          >
            C4 {c4 ? '✓' : '—'}
          </span>
        </div>
        {c4 && snapshot?.status === 'active' && (
          <span className="hidden md:inline px-1.5 py-0.2 bg-[#b91c1c] text-white text-[10px] font-bold animate-pulse">
            CONTAINMENT READY IN F10
          </span>
        )}
      </div>

      {/* Live AI Suspect Gauges */}
      {snapshot && (
        <div className="hidden lg:flex items-center gap-3 text-[11px] font-mono border-l border-[#808080] pl-3">
          <div className="flex items-center gap-1.5" title={`HELPER Composure: ${snapshot.trust}%`}>
            <span className="text-[#374151] font-bold">TRUST:</span>
            <div className="w-16 h-2.5 bg-[#111416] p-0.5 border border-[#808080] flex">
              <div
                className={`h-full transition-all ${
                  snapshot.trust > 45 ? 'bg-[#22c55e]' : snapshot.trust > 25 ? 'bg-[#eab308]' : 'bg-[#ef4444] animate-pulse'
                }`}
                style={{ width: `${snapshot.trust}%` }}
              />
            </div>
            <span className={`font-bold ${snapshot.trust <= 35 ? 'text-[#b91c1c]' : 'text-[#374151]'}`}>
              {snapshot.trust}%
            </span>
          </div>

          <div className="flex items-center gap-1.5" title={`Anomaly / Lock Agitation: ${snapshot.fear}%`}>
            <span className="text-[#374151] font-bold">FEAR:</span>
            <div className="w-16 h-2.5 bg-[#111416] p-0.5 border border-[#808080] flex">
              <div
                className="h-full bg-[#ef4444] transition-all"
                style={{ width: `${Math.min(100, snapshot.fear * 3)}%` }}
              />
            </div>
            <span className={`font-bold ${snapshot.fear >= 15 ? 'text-[#b91c1c]' : 'text-[#374151]'}`}>
              {snapshot.fear}%
            </span>
          </div>
        </div>
      )}

      {/* Navigation Links */}
      <nav className="hidden md:flex items-center gap-1.5 text-xs font-sans">
        <button
          type="button"
          onClick={onOpenSettings}
          className="text-[#1a1c1c] px-2.5 py-0.5 hover:bg-[#dfdfdf] cursor-pointer rounded-xs"
        >
          System Properties
        </button>

        <button
          type="button"
          onClick={onToggleScanlines}
          className={`px-2.5 py-0.5 text-xs font-medium cursor-pointer rounded-xs border ${
            scanlines
              ? 'bg-[#008080] text-white border-[#004f4f] font-bold'
              : 'bg-[#d4d0c8] text-[#4b5563] border-[#9ca3af]'
          }`}
          title="Toggle CRT Scanline Overlay"
        >
          CRT Overlay: {scanlines ? 'ON' : 'OFF'}
        </button>
      </nav>

      {/* Top window control cluster */}
      <div className="flex items-center gap-1.5">
        <button
          type="button"
          aria-label="System Settings"
          onClick={onOpenSettings}
          className="w-5 h-5 bg-[#c0c0c0] flex items-center justify-center text-[#1a1c1c] w98-bevel-raised-sm active:w98-bevel-sunken-sm hover:bg-[#dfdfdf] cursor-pointer"
          title="System Settings"
        >
          <RetroIcon name="settings" size={12} />
        </button>
      </div>
    </header>
  );
};
