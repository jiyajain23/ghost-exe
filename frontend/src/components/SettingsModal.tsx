import { useState, type FC } from 'react';
import { RetroIcon } from './RetroIcons';
import type { RunState } from '../api/types';

interface SettingsModalProps {
  snapshot: RunState | null;
  reduced: boolean;
  scanlines: boolean;
  onToggleReduced: (val: boolean) => void;
  onToggleScanlines: (val: boolean) => void;
  onClose: () => void;
  onReload?: () => void;
  onRestart?: () => void;
}

export const SettingsModal: FC<SettingsModalProps> = ({
  snapshot,
  reduced,
  scanlines,
  onToggleReduced,
  onToggleScanlines,
  onClose,
  onReload,
  onRestart,
}) => {
  const [tab, setTab] = useState<'general' | 'display' | 'system'>('general');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-3 select-none">
      <div className="w-full max-w-md bg-[#c0c0c0] w98-bevel-raised shadow-2xl flex flex-col font-sans text-xs">
        {/* Titlebar */}
        <div className="h-6 px-1.5 py-0.5 bg-gradient-to-r from-[#000080] via-[#006565] to-[#1084d0] flex items-center justify-between text-white select-none">
          <div className="flex items-center gap-1.5 overflow-hidden">
            <RetroIcon name="settings" size={12} className="text-[#76d6d5]" />
            <span className="font-bold text-xs text-white tracking-wide truncate">
              System Properties
            </span>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close settings"
            className="w-4 h-4 bg-[#c0c0c0] w98-bevel-raised-sm text-black flex items-center justify-center text-[10px] font-bold active:w98-bevel-sunken-sm hover:bg-[#dfdfdf] cursor-pointer"
          >
            ×
          </button>
        </div>

        {/* Tab Row */}
        <div className="px-2 pt-2 bg-[#c0c0c0] flex gap-1 border-b border-[#808080]">
          <button
            type="button"
            onClick={() => setTab('general')}
            className={`px-3 py-1 text-xs font-bold ${tab === 'general' ? 'w98-tab-active -mb-[1px] bg-[#c0c0c0]' : 'w98-tab-inactive text-[#404040]'}`}
          >
            General
          </button>
          <button
            type="button"
            onClick={() => setTab('display')}
            className={`px-3 py-1 text-xs font-bold ${tab === 'display' ? 'w98-tab-active -mb-[1px] bg-[#c0c0c0]' : 'w98-tab-inactive text-[#404040]'}`}
          >
            Display &amp; CRT
          </button>
          <button
            type="button"
            onClick={() => setTab('system')}
            className={`px-3 py-1 text-xs font-bold ${tab === 'system' ? 'w98-tab-active -mb-[1px] bg-[#c0c0c0]' : 'w98-tab-inactive text-[#404040]'}`}
          >
            Archive State
          </button>
        </div>

        {/* Tab Body */}
        <div className="p-3 bg-[#c0c0c0] min-h-[220px] flex flex-col justify-between">
          {tab === 'general' && (
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <RetroIcon name="computer" size={36} />
                <div className="space-y-1">
                  <div className="font-bold text-sm text-[#006565]">VesperOS 2003 (Archive Edition)</div>
                  <div className="text-[11px] text-[#404040]">Sub-Base 09 Briar Annex System</div>
                  <div className="text-[11px] text-[#404040]">Build 2003.10.31-PROD</div>
                </div>
              </div>

              <div className="p-2 w98-bevel-sunken bg-white space-y-1 font-mono text-[11px]">
                <div>Operator: <span className="font-bold text-[#000080]">Guest Investigator</span></div>
                <div>Station: <span className="font-bold text-[#000080]">ADA-MERCER-03</span></div>
                <div>Memory: <span className="font-bold text-[#006565]">640 KB Base / 16 MB Extended</span></div>
                <div>Sector Parity: <span className="font-bold text-[#ba1a1a]">TAMPER DETECTED (0x2317)</span></div>
              </div>
            </div>
          )}

          {tab === 'display' && (
            <div className="space-y-3">
              <div className="text-xs font-bold text-[#006565]">Visual Atmosphere &amp; CRT Filters:</div>
              <div className="space-y-2 p-2 w98-bevel-sunken bg-[#f4f3f3]">
                <label className="flex items-center gap-2 cursor-pointer font-medium">
                  <input
                    type="checkbox"
                    checked={scanlines}
                    onChange={e => onToggleScanlines(e.target.checked)}
                    className="accent-[#008080]"
                  />
                  <span>Enable CRT Scanline Filter &amp; Vignette</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer font-medium">
                  <input
                    type="checkbox"
                    checked={reduced}
                    onChange={e => onToggleReduced(e.target.checked)}
                    className="accent-[#008080]"
                  />
                  <span>Reduced Motion (Disables CRT flicker &amp; spectral glitches)</span>
                </label>
              </div>
              <p className="text-[10px] text-[#606060] italic">
                Reduced motion is automatically synchronized with your operating system accessibility preferences.
              </p>
            </div>
          )}

          {tab === 'system' && (
            <div className="space-y-3">
              <div className="text-xs font-bold text-[#006565]">Active Investigation Telemetry:</div>
              <div className="p-2 w98-bevel-sunken bg-white space-y-1 font-mono text-[11px]">
                <div>Run Index: <span className="font-bold text-[#006565]">#{snapshot ? String(snapshot.run_index).padStart(3, '0') : 'NONE'}</span></div>
                <div>Documents Opened: <span className="font-bold text-[#006565]">{snapshot?.opened_file_ids.length ?? 0}</span></div>
                <div>Clues Collected: <span className="font-bold text-[#006565]">{snapshot?.clues.length ?? 0}</span></div>
                <div>HELPER Exchanges: <span className="font-bold text-[#006565]">{snapshot?.helper_chat_turns ?? 0}</span></div>
                <div>Photo Choice: <span className="font-bold text-[#ba1a1a]">{snapshot?.photo_choice ?? 'PENDING'}</span></div>
              </div>

              <div className="flex gap-2 pt-1">
                {onReload && (
                  <button
                    type="button"
                    onClick={onReload}
                    className="px-2 py-1 w98-btn text-[11px] flex-1"
                  >
                    Reload Current Run
                  </button>
                )}
                {onRestart && (
                  <button
                    type="button"
                    onClick={onRestart}
                    className="px-2 py-1 w98-btn text-[#ba1a1a] text-[11px] flex-1 font-bold"
                  >
                    Restart Investigation
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-3 border-t border-[#808080] flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1 w98-btn text-xs font-bold"
            >
              OK
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1 w98-btn text-xs"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
