import { useEffect, useRef, type FC } from 'react';
import { RetroIcon } from './RetroIcons';
import type { AppId } from '../api/types';

interface StartMenuProps {
  isOpen: boolean;
  onClose: () => void;
  onLaunch: (id: AppId) => void;
  onOpenSettings: () => void;
  onRestartInvestigation: () => void;
}

export const StartMenu: FC<StartMenuProps> = ({
  isOpen,
  onClose,
  onLaunch,
  onOpenSettings,
  onRestartInvestigation,
}) => {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('mousedown', handleClickOutside);
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('mousedown', handleClickOutside);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      ref={menuRef}
      className="fixed bottom-[32px] left-1 z-50 flex bg-[#c0c0c0] w98-bevel-raised shadow-2xl select-none min-w-[210px]"
    >
      {/* Left Vertical Banner */}
      <div className="w-7 bg-gradient-to-t from-[#000080] via-[#006565] to-[#1084d0] flex items-end justify-center pb-3 text-white">
        <span
          className="text-xs font-bold tracking-widest text-[#e1e2e5] uppercase whitespace-nowrap"
          style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}
        >
          Vesper<strong className="text-white">OS 2003</strong>
        </span>
      </div>

      {/* Menu Options List */}
      <div className="flex-1 py-1 flex flex-col font-sans text-xs">
        <button
          type="button"
          onClick={() => { onLaunch('helper'); onClose(); }}
          className="flex items-center gap-2.5 px-3 py-1.5 hover:bg-[#000080] hover:text-white text-[#1a1c1c] text-left cursor-pointer group"
        >
          <RetroIcon name="skull" size={16} />
          <span className="font-bold">GHOST.EXE (HELPER)</span>
        </button>

        <button
          type="button"
          onClick={() => { onLaunch('explorer'); onClose(); }}
          className="flex items-center gap-2.5 px-3 py-1.5 hover:bg-[#000080] hover:text-white text-[#1a1c1c] text-left cursor-pointer group"
        >
          <RetroIcon name="folder" size={16} />
          <span>File Explorer</span>
        </button>

        <button
          type="button"
          onClick={() => { onLaunch('mail'); onClose(); }}
          className="flex items-center gap-2.5 px-3 py-1.5 hover:bg-[#000080] hover:text-white text-[#1a1c1c] text-left cursor-pointer group"
        >
          <RetroIcon name="mail" size={16} />
          <span>Mail / Log Viewer</span>
        </button>

        <div className="h-px bg-[#808080] my-1 mx-1 border-b border-white" />

        <button
          type="button"
          onClick={() => { onOpenSettings(); onClose(); }}
          className="flex items-center gap-2.5 px-3 py-1.5 hover:bg-[#000080] hover:text-white text-[#1a1c1c] text-left cursor-pointer group"
        >
          <RetroIcon name="settings" size={16} />
          <span>Settings...</span>
        </button>

        <div className="h-px bg-[#808080] my-1 mx-1 border-b border-white" />

        <button
          type="button"
          onClick={() => { onRestartInvestigation(); onClose(); }}
          className="flex items-center gap-2.5 px-3 py-1.5 hover:bg-[#ba1a1a] hover:text-white text-[#ba1a1a] text-left cursor-pointer group font-bold"
        >
          <RetroIcon name="power" size={16} className="text-[#ba1a1a] group-hover:text-white" />
          <span>Restart Investigation...</span>
        </button>
      </div>
    </div>
  );
};
