import { useEffect, useRef } from 'react';
import type { RunState } from '../api/types';

export function EndingScreen({ snapshot, onRestart }: { snapshot: RunState; onRestart: () => void }) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { heading.current?.focus(); }, []);
  if (snapshot.status !== 'completed' || !snapshot.ending_presentation) return null;
  const ending = snapshot.ending_presentation;
  return (
    <main aria-labelledby="ending-title" className="min-h-screen w-full bg-[#0c0f11] text-white p-6 flex flex-col items-center justify-center gap-6 overflow-y-auto">
      <p role="status">INVESTIGATION COMPLETE</p>
      <h1 id="ending-title" ref={heading} tabIndex={-1} className="text-3xl font-bold">{ending.title}</h1>
      <blockquote className="max-w-2xl text-lg">{ending.final_line}</blockquote>
      <p className="whitespace-pre-wrap break-words max-w-2xl font-mono">{ending.narrative}</p>
      <button type="button" className="w98-btn p-3 text-black" onClick={onRestart}>Restart Investigation</button>
    </main>
  );
}
