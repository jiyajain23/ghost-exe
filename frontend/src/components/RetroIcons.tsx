import type { FC, SVGProps } from 'react';

export type IconName =
  | 'terminal'
  | 'computer'
  | 'folder'
  | 'folder-open'
  | 'folder-special'
  | 'document'
  | 'mail'
  | 'settings'
  | 'recycle-bin'
  | 'warning'
  | 'skull'
  | 'memory'
  | 'bug-report'
  | 'sensors'
  | 'lan'
  | 'lock'
  | 'check'
  | 'bolt'
  | 'play'
  | 'history'
  | 'print'
  | 'visibility-off'
  | 'data-array'
  | 'speaker'
  | 'close'
  | 'minimize'
  | 'maximize'
  | 'help'
  | 'power';

interface RetroIconProps extends SVGProps<SVGSVGElement> {
  name: IconName;
  size?: number | string;
  className?: string;
}

export const RetroIcon: FC<RetroIconProps> = ({ name, size = 16, className = '', ...props }) => {
  switch (name) {
    case 'terminal':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <rect x="1" y="2" width="14" height="12" rx="1" fill="#121517" stroke="currentColor" strokeWidth="1" />
          <path d="M4 5L7 8L4 11" stroke="#33ff66" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
          <rect x="8" y="10" width="4" height="1.5" fill="#33ff66" />
        </svg>
      );

    case 'computer':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <rect x="2" y="2" width="12" height="9" rx="0.5" fill="#d4d0c8" stroke="#404040" strokeWidth="1" />
          <rect x="3.5" y="3.5" width="9" height="6" fill="#008080" />
          <rect x="6" y="11" width="4" height="2" fill="#d4d0c8" stroke="#404040" strokeWidth="0.8" />
          <rect x="3" y="13" width="10" height="2" rx="0.5" fill="#d4d0c8" stroke="#404040" strokeWidth="0.8" />
        </svg>
      );

    case 'folder':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <path d="M1 3.5C1 3.2 1.2 3 1.5 3H6L7.5 5H14.5C14.8 5 15 5.2 15 5.5V12.5C15 12.8 14.8 13 14.5 13H1.5C1.2 13 1 12.8 1 12.5V3.5Z" fill="#e5a93c" stroke="#8c6218" strokeWidth="1" />
          <rect x="2" y="5.5" width="12" height="6.5" rx="0.5" fill="#ffca58" />
        </svg>
      );

    case 'folder-open':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <path d="M1 3.5H6L7.5 5H14V8H2V4H1V3.5Z" fill="#c48a20" />
          <polygon points="1.5,13.5 4,7 15.5,7 13,13.5" fill="#ffca58" stroke="#8c6218" strokeWidth="1" strokeLinejoin="round" />
        </svg>
      );

    case 'folder-special':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <path d="M1 3.5H6L7.5 5H14.5V12.5H1V3.5Z" fill="#008080" stroke="#004040" strokeWidth="1" />
          <rect x="2" y="5.5" width="12" height="6" fill="#76d6d5" />
          <circle cx="8" cy="8.5" r="2" fill="#ffffff" />
        </svg>
      );

    case 'document':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <polygon points="3,1 10,1 13,4 13,15 3,15" fill="#fafafa" stroke="#404040" strokeWidth="1" strokeLinejoin="round" />
          <polygon points="10,1 10,4 13,4" fill="#c0c0c0" stroke="#404040" strokeWidth="1" />
          <line x1="5" y1="6" x2="11" y2="6" stroke="#808080" strokeWidth="1" />
          <line x1="5" y1="8.5" x2="11" y2="8.5" stroke="#808080" strokeWidth="1" />
          <line x1="5" y1="11" x2="9" y2="11" stroke="#808080" strokeWidth="1" />
        </svg>
      );

    case 'mail':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <rect x="1.5" y="3.5" width="13" height="9" rx="0.5" fill="#ffffff" stroke="#404040" strokeWidth="1" />
          <path d="M2 4L8 9L14 4" stroke="#404040" strokeWidth="1" fill="none" />
        </svg>
      );

    case 'settings':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <circle cx="8" cy="8" r="6" fill="#808080" stroke="#404040" strokeWidth="1" />
          <rect x="6.5" y="1" width="3" height="14" rx="0.5" fill="#606060" />
          <rect x="1" y="6.5" width="14" height="3" rx="0.5" fill="#606060" />
          <circle cx="8" cy="8" r="3.5" fill="#c0c0c0" stroke="#404040" strokeWidth="1" />
          <circle cx="8" cy="8" r="1.5" fill="#ffffff" />
        </svg>
      );

    case 'recycle-bin':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <rect x="3.5" y="4" width="9" height="10.5" rx="0.5" fill="#d0d0d0" stroke="#404040" strokeWidth="1" />
          <rect x="2" y="2" width="12" height="2" rx="0.5" fill="#909090" stroke="#404040" strokeWidth="1" />
          <line x1="6" y1="6" x2="6" y2="12" stroke="#606060" strokeWidth="1" />
          <line x1="8" y1="6" x2="8" y2="12" stroke="#606060" strokeWidth="1" />
          <line x1="10" y1="6" x2="10" y2="12" stroke="#606060" strokeWidth="1" />
        </svg>
      );

    case 'warning':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <polygon points="8,1.5 15,14 1,14" fill="#facc15" stroke="#854d0e" strokeWidth="1" strokeLinejoin="round" />
          <rect x="7" y="6" width="2" height="4" rx="0.5" fill="#000000" />
          <circle cx="8" cy="11.5" r="1" fill="#000000" />
        </svg>
      );

    case 'skull':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <path d="M4 2.5C4 1.8 5 1 8 1C11 1 12 1.8 12 2.5V8H11V11H9.5V13.5H6.5V11H5V8H4V2.5Z" fill="#ff4444" stroke="#990000" strokeWidth="0.8" />
          <circle cx="6" cy="5.5" r="1.3" fill="#000000" />
          <circle cx="10" cy="5.5" r="1.3" fill="#000000" />
          <polygon points="8,7 7.5,8.5 8.5,8.5" fill="#000000" />
          <line x1="7" y1="11" x2="7" y2="13.5" stroke="#000000" strokeWidth="1" />
          <line x1="9" y1="11" x2="9" y2="13.5" stroke="#000000" strokeWidth="1" />
        </svg>
      );

    case 'memory':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <rect x="3" y="3" width="10" height="10" rx="0.5" fill="#1e293b" stroke="#76d6d5" strokeWidth="1" />
          <rect x="5.5" y="5.5" width="5" height="5" fill="#0f766e" />
          <line x1="5" y1="1" x2="5" y2="3" stroke="#76d6d5" strokeWidth="1" />
          <line x1="8" y1="1" x2="8" y2="3" stroke="#76d6d5" strokeWidth="1" />
          <line x1="11" y1="1" x2="11" y2="3" stroke="#76d6d5" strokeWidth="1" />
          <line x1="5" y1="13" x2="5" y2="15" stroke="#76d6d5" strokeWidth="1" />
          <line x1="8" y1="13" x2="8" y2="15" stroke="#76d6d5" strokeWidth="1" />
          <line x1="11" y1="13" x2="11" y2="15" stroke="#76d6d5" strokeWidth="1" />
        </svg>
      );

    case 'bug-report':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <ellipse cx="8" cy="9.5" rx="4" ry="4.5" fill="#ef4444" stroke="#7f1d1d" strokeWidth="0.8" />
          <circle cx="8" cy="4" r="2.2" fill="#991b1b" />
          <line x1="4" y1="8" x2="1.5" y2="7" stroke="#450a0a" strokeWidth="1.2" strokeLinecap="round" />
          <line x1="12" y1="8" x2="14.5" y2="7" stroke="#450a0a" strokeWidth="1.2" strokeLinecap="round" />
          <line x1="4" y1="10" x2="1.5" y2="10" stroke="#450a0a" strokeWidth="1.2" strokeLinecap="round" />
          <line x1="12" y1="10" x2="14.5" y2="10" stroke="#450a0a" strokeWidth="1.2" strokeLinecap="round" />
        </svg>
      );

    case 'sensors':
    case 'lan':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <rect x="2" y="2" width="4" height="3" rx="0.5" fill="#008080" />
          <rect x="10" y="2" width="4" height="3" rx="0.5" fill="#008080" />
          <rect x="6" y="11" width="4" height="3" rx="0.5" fill="#008080" />
          <line x1="4" y1="5" x2="4" y2="8" stroke="#004040" strokeWidth="1" />
          <line x1="12" y1="5" x2="12" y2="8" stroke="#004040" strokeWidth="1" />
          <line x1="4" y1="8" x2="12" y2="8" stroke="#004040" strokeWidth="1" />
          <line x1="8" y1="8" x2="8" y2="11" stroke="#004040" strokeWidth="1" />
        </svg>
      );

    case 'lock':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <path d="M5 6V4A3 3 0 0 1 11 4V6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none" />
          <rect x="3" y="6" width="10" height="8" rx="1" fill="#e5a93c" stroke="#8c6218" strokeWidth="1" />
          <circle cx="8" cy="10" r="1" fill="#000000" />
        </svg>
      );

    case 'check':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <path d="M3 8L6.5 11.5L13 4" stroke="#22c55e" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        </svg>
      );

    case 'bolt':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <polygon points="9,1 3,9 8,9 7,15 13,7 8,7" fill="#facc15" stroke="#854d0e" strokeWidth="1" strokeLinejoin="round" />
        </svg>
      );

    case 'play':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <polygon points="4,2.5 14,8 4,13.5" fill="#008080" stroke="#004040" strokeWidth="0.8" strokeLinejoin="round" />
        </svg>
      );

    case 'history':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" fill="none" />
          <polyline points="8,4.5 8,8 11,8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        </svg>
      );

    case 'print':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <rect x="4" y="2" width="8" height="4" rx="0.5" fill="#f1f5f9" stroke="#475569" strokeWidth="1" />
          <rect x="2" y="5.5" width="12" height="6" rx="0.5" fill="#94a3b8" stroke="#334155" strokeWidth="1" />
          <rect x="4" y="9" width="8" height="5" fill="#ffffff" stroke="#334155" strokeWidth="1" />
        </svg>
      );

    case 'visibility-off':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <path d="M2 8C3.5 5 6 3 8 3C10 3 12.5 5 14 8C12.5 11 10 13 8 13C6 13 3.5 11 2 8Z" stroke="currentColor" strokeWidth="1.2" fill="none" />
          <circle cx="8" cy="8" r="2.5" fill="currentColor" />
          <line x1="2" y1="14" x2="14" y2="2" stroke="#ef4444" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      );

    case 'data-array':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <path d="M4 3H2V13H4M12 3H14V13H12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none" />
          <rect x="5.5" y="7" width="5" height="2" rx="0.5" fill="currentColor" />
        </svg>
      );

    case 'speaker':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <polygon points="2,6 5.5,6 9,3 9,13 5.5,10 2,10" fill="#404040" stroke="#202020" strokeWidth="0.8" strokeLinejoin="round" />
          <path d="M11 5.5C12 6.5 12 9.5 11 10.5M13 3.5C14.5 5 14.5 11 13 12.5" stroke="#404040" strokeWidth="1.2" strokeLinecap="round" fill="none" />
        </svg>
      );

    case 'close':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <path d="M4 4L12 12M12 4L4 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      );

    case 'minimize':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <line x1="3" y1="12" x2="13" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      );

    case 'maximize':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <rect x="3" y="3" width="10" height="10" stroke="currentColor" strokeWidth="1.5" fill="none" />
        </svg>
      );

    case 'power':
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <path d="M5 4.5A5.5 5.5 0 1 0 11 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" fill="none" />
          <line x1="8" y1="2" x2="8" y2="7.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      );

    case 'help':
    default:
      return (
        <svg width={size} height={size} viewBox="0 0 16 16" fill="currentColor" className={className} {...props}>
          <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1" fill="none" />
          <path d="M6 6C6 4.5 7 4 8 4C9 4 10 4.5 10 5.5C10 6.5 9 7 8 7.5V9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" fill="none" />
          <circle cx="8" cy="11" r="0.75" fill="currentColor" />
        </svg>
      );
  }
};
