import type { FC } from 'react';
import { RetroIcon } from './RetroIcons';

interface TopNavBarProps {
  scanlines: boolean;
  onToggleScanlines: () => void;
  onOpenSettings?: () => void;
}

export const TopNavBar: FC<TopNavBarProps> = ({
  scanlines,
  onToggleScanlines,
  onOpenSettings,
}) => {
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
