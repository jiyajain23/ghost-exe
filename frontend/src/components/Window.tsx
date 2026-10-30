import { useEffect, useRef, useState, type FC, type ReactNode } from 'react';
import type { AppId } from '../api/types';
import { RetroIcon } from './RetroIcons';

interface WindowProps {
  id: AppId;
  title: string;
  active: boolean;
  order: number;
  onFocus: () => void;
  onClose: () => void;
  children: ReactNode;
}

export const Window: FC<WindowProps> = ({
  id,
  title,
  active,
  order,
  onFocus,
  onClose,
  children,
}) => {
  const titleRef = useRef<HTMLButtonElement>(null);
  const [maximized, setMaximized] = useState(false);

  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  const getWindowIcon = () => {
    switch (id) {
      case 'helper':
        return <RetroIcon name="skull" size={15} className="text-[#76d6d5] shrink-0" />;
      case 'explorer':
        return <RetroIcon name="folder" size={15} className="shrink-0" />;
      case 'mail':
        return <RetroIcon name="mail" size={15} className="shrink-0" />;
      default:
        return <RetroIcon name="computer" size={15} className="shrink-0" />;
    }
  };

  // Default positioning for comfortable multi-window layout
  const getWindowPositionClass = () => {
    if (maximized) {
      return 'fixed inset-2 md:inset-4 bottom-[36px] z-30';
    }
    switch (id) {
      case 'helper':
        return 'absolute top-1 right-1 w-[460px] max-w-[calc(100vw-110px)] h-[calc(100%-12px)] min-h-[460px]';
      case 'explorer':
        return 'absolute top-1 left-1 w-[680px] max-w-[calc(100vw-110px)] h-[calc(100%-20px)] min-h-[460px]';
      case 'mail':
        return 'absolute top-6 left-6 w-[640px] max-w-[calc(100vw-120px)] h-[calc(100%-40px)] min-h-[440px]';
      default:
        return 'absolute top-4 left-4 w-[600px] h-[500px]';
    }
  };

  return (
    <section
      className={`window window-${id} ${active ? 'active' : 'inactive'} ${getWindowPositionClass()} flex flex-col bg-[#c0c0c0] w98-bevel-raised shadow-2xl overflow-hidden select-none`}
      style={{ zIndex: order + (active ? 20 : 10) }}
      aria-labelledby={`${id}-title`}
      onPointerDown={onFocus}
      onFocusCapture={onFocus}
    >
      {/* Authentic Windows 98 Titlebar */}
      <header
        onDoubleClick={() => setMaximized(!maximized)}
        className={`h-7 px-2 py-0.5 flex items-center justify-between text-white select-none cursor-move ${
          active
            ? 'bg-gradient-to-r from-[#000080] via-[#006565] to-[#1084d0]'
            : 'bg-gradient-to-r from-[#71717a] to-[#a1a1aa]'
        }`}
      >
        <button
          ref={titleRef}
          id={`${id}-title`}
          onClick={onFocus}
          className="flex items-center gap-2 overflow-hidden text-left bg-transparent border-0 p-0 text-white font-bold text-xs tracking-wide cursor-pointer focus:outline-none"
        >
          {getWindowIcon()}
          <span className="truncate drop-shadow-[0_1px_1px_rgba(0,0,0,0.8)]">
            {title}
          </span>
        </button>

        {/* Titlebar Control Buttons */}
        <div className="flex items-center gap-1 shrink-0 ml-2">
          <button
            type="button"
            aria-label={`Minimize ${title}`}
            onClick={(e) => {
              e.stopPropagation();
              onClose();
            }}
            className="w-5 h-5 bg-[#c0c0c0] w98-bevel-raised-sm text-black flex items-center justify-center text-xs font-bold active:w98-bevel-sunken-sm hover:bg-[#dfdfdf] cursor-pointer"
            title="Minimize"
          >
            _
          </button>
          <button
            type="button"
            aria-label={`Maximize ${title}`}
            onClick={(e) => {
              e.stopPropagation();
              setMaximized(!maximized);
            }}
            className="w-5 h-5 bg-[#c0c0c0] w98-bevel-raised-sm text-black flex items-center justify-center text-xs font-bold active:w98-bevel-sunken-sm hover:bg-[#dfdfdf] cursor-pointer"
            title={maximized ? 'Restore Window' : 'Maximize Window'}
          >
            {maximized ? '❐' : '□'}
          </button>
          <button
            type="button"
            aria-label={`Close ${title}`}
            onClick={(e) => {
              e.stopPropagation();
              onClose();
            }}
            className="w-5 h-5 bg-[#c0c0c0] w98-bevel-raised-sm text-black flex items-center justify-center text-xs font-bold active:w98-bevel-sunken-sm hover:bg-[#ef4444] hover:text-white cursor-pointer"
            title="Close"
          >
            ×
          </button>
        </div>
      </header>

      {/* Application Menu Strip */}
      <div className="px-2 py-0.5 bg-[#c0c0c0] border-b border-[#808080] flex gap-3 text-xs text-[#1a1c1c] font-sans">
        <span className="hover:bg-[#000080] hover:text-white px-1.5 py-0.5 cursor-pointer rounded-xs">
          <u className="font-bold">F</u>ile
        </span>
        <span className="hover:bg-[#000080] hover:text-white px-1.5 py-0.5 cursor-pointer rounded-xs">
          <u className="font-bold">E</u>dit
        </span>
        <span className="hover:bg-[#000080] hover:text-white px-1.5 py-0.5 cursor-pointer rounded-xs">
          <u className="font-bold">V</u>iew
        </span>
        <span className="hover:bg-[#000080] hover:text-white px-1.5 py-0.5 cursor-pointer rounded-xs">
          <u className="font-bold">H</u>elp
        </span>
      </div>

      {/* Window Body Workspace */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden bg-[#c0c0c0]">
        {children}
      </div>
    </section>
  );
};
