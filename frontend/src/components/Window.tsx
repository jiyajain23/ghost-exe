import { useEffect, useRef, type ReactNode } from 'react';
import type { AppId } from '../api/types';
export function Window({ id, title, active, order, onFocus, onClose, children }: {
  id: AppId; title: string; active: boolean; order: number;
  onFocus: () => void; onClose: () => void; children: ReactNode;
}) {
  const titleRef = useRef<HTMLButtonElement>(null);
  useEffect(() => { titleRef.current?.focus(); }, []);
  return <section className={`window window-${id} ${active ? 'active' : 'inactive'}`} style={{ zIndex: order + 1 }}
    aria-labelledby={`${id}-title`} onPointerDown={onFocus} onFocusCapture={onFocus}>
    <header className="titlebar"><button ref={titleRef} id={`${id}-title`} className="window-title" onClick={onFocus}>
      <span className={`mini-icon icon-${id}`} aria-hidden="true" />{title}</button>
      <button className="close-button" aria-label={`Close ${title}`} onClick={event => { event.stopPropagation(); onClose(); }}>×</button>
    </header>{children}
  </section>;
}
