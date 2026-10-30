import { useEffect, useRef, useState, type FC } from 'react';
import { RetroIcon } from '../components/RetroIcons';

export interface Exchange {
  speaker: 'HELPER' | 'YOU';
  text: string;
}

interface HelperProps {
  messages: Exchange[];
  busy: boolean;
  sending: boolean;
  status: string;
  runIndex?: number;
  onSend: (message: string, done: () => void) => void;
}

const QUICK_PROMPTS = [
  'What happened to Ada?',
  'What can I read next?',
  'Where are the archive logs?',
  'Why is the clock frozen at 23:17?',
];

export const Helper: FC<HelperProps> = ({
  messages,
  busy,
  sending,
  status,
  runIndex = 1,
  onSend,
}) => {
  const [message, setMessage] = useState('');
  const [showTelemetry, setShowTelemetry] = useState(false);
  const historyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (historyRef.current) {
      historyRef.current.scrollTop = historyRef.current.scrollHeight;
    }
  }, [messages, sending]);

  const handleSubmit = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || busy || sending) return;
    onSend(trimmed, () => setMessage(''));
  };

  return (
    <div className="flex-1 flex flex-col h-full min-h-0 bg-[#c0c0c0] font-sans text-xs select-none">
      {/* Sub-Header Status HUD */}
      <div className="flex flex-wrap items-center justify-between gap-2 p-1.5 bg-[#d4d0c8] border-b border-[#808080] text-xs font-mono">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 font-bold text-[#006565]">
            <span className="w-2 h-2 rounded-full bg-[#22c55e] inline-block" />
            ONLINE (127.0.0.1:8000)
          </span>
          <span className="text-[#808080]">|</span>
          <span className="text-[#b91c1c] font-bold">SIGNAL: 83.4% UNSTABLE</span>
          <span className="text-[#808080]">|</span>
          <span className="text-[#4b5563]">RUN #{String(runIndex).padStart(3, '0')}</span>
        </div>

        <button
          type="button"
          onClick={() => setShowTelemetry(!showTelemetry)}
          className={`px-2 py-0.5 text-[11px] font-mono font-bold cursor-pointer ${
            showTelemetry ? 'w98-bevel-sunken bg-white text-[#006565]' : 'w98-bevel-raised bg-[#c0c0c0] text-[#404040]'
          }`}
        >
          {showTelemetry ? '▲ HIDE TELEMETRY' : '▼ SENSOR TELEMETRY'}
        </button>
      </div>

      {/* Collapsible Telemetry Rail */}
      {showTelemetry && (
        <div className="p-2 bg-[#e5e7eb] border-b border-[#808080] font-mono text-xs grid grid-cols-1 sm:grid-cols-3 gap-2">
          <div className="p-2 bg-white w98-bevel-sunken-sm space-y-1">
            <div className="text-[10px] text-[#6b7280] font-bold">MEMORY BUFFER (0x400):</div>
            <div className="grid grid-cols-4 gap-1 text-center font-bold text-[11px]">
              <span className="bg-[#fee2e2] text-[#b91c1c]">00FF</span>
              <span className="text-[#9ca3af]">0000</span>
              <span className="text-[#9ca3af]">A1C2</span>
              <span className="bg-[#b91c1c] text-white">DEAD</span>
            </div>
          </div>
          <div className="p-2 bg-white w98-bevel-sunken-sm space-y-1">
            <div className="text-[10px] text-[#6b7280] font-bold">CARRIER WAVE:</div>
            <div className="text-[#b91c1c] font-bold">83.4% DEVIATION</div>
            <div className="w-full h-2.5 bg-[#d1d5db] flex gap-0.5 p-0.5">
              <div className="h-full w-4 bg-[#008080]" />
              <div className="h-full w-4 bg-[#008080]" />
              <div className="h-full w-4 bg-[#b91c1c]" />
            </div>
          </div>
          <div className="p-2 bg-white w98-bevel-sunken-sm space-y-1">
            <div className="text-[10px] text-[#6b7280] font-bold">SENSOR STATE:</div>
            <div className="text-[#006565] font-bold">COM1 / RECEPTOR DETECTED</div>
            <div className="text-[10px] text-[#4b5563]">Anomalous thread registered at 0x2317.</div>
          </div>
        </div>
      )}

      {/* Main Terminal Screen Canvas */}
      <div className="flex-1 flex flex-col min-h-0 p-2 bg-[#c0c0c0] overflow-hidden">
        <div className="flex-1 flex flex-col min-h-0 bg-[#0c0f11] w98-bevel-sunken p-3 relative overflow-hidden text-emerald-400">
          {/* Subtle Scanlines */}
          <div className="absolute inset-0 scanlines pointer-events-none opacity-20 z-10" />

          {/* Terminal Screen Header */}
          <div className="relative z-20 border-b border-[#1f2937] pb-1.5 mb-2 text-xs text-[#9ca3af] flex justify-between items-center shrink-0 font-mono">
            <span className="text-[#76d6d5] font-bold">
              [TTY_04: /DEV/HELPER_DAEMON]
            </span>
            <span className="text-[#ef4444] font-bold flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#ef4444] animate-ping inline-block" />
              INTERROGATION ACTIVE
            </span>
          </div>

          {/* Scrollable Transcript Feed - High Legibility */}
          <div
            ref={historyRef}
            tabIndex={0}
            role="log"
            aria-label="HELPER conversation transcript"
            className="relative z-20 flex-1 overflow-y-auto space-y-3 pr-2 font-mono text-[13px] leading-relaxed focus:outline-none"
          >
            <div className="text-[#4ade80] text-xs pb-1 border-b border-[#1f2937] opacity-80">
              --- ARCHIVE RESTORED: RESIDENT HELPER DAEMON DETECTED AT MEMORY 0xDEADBEEF ---
            </div>

            {messages.map((entry, index) => {
              const isHelper = entry.speaker === 'HELPER';
              const isAnomaly =
                entry.text.toLowerCase().includes('negative') ||
                entry.text.toLowerCase().includes('door b') ||
                entry.text.toLowerCase().includes('room 04') ||
                entry.text.toLowerCase().includes('remember') ||
                entry.text.toLowerCase().includes('last time');

              return (
                <div
                  key={index}
                  className={`flex flex-col gap-1 p-2 rounded-xs ${
                    !isHelper
                      ? 'bg-[#1e1b4b]/60 border-l-4 border-[#6366f1] text-white ml-4'
                      : isAnomaly
                      ? 'bg-[#3b0707]/70 border-l-4 border-[#ef4444] text-[#fecaca]'
                      : 'bg-[#0f172a]/50 border-l-4 border-[#0d9488] text-[#dcfce7] mr-4'
                  }`}
                >
                  <div className="flex items-center gap-2 text-xs font-bold">
                    <span className="text-[#6b7280] font-normal">
                      [23:17:{String(index * 3).padStart(2, '0')}]
                    </span>
                    <span className={isHelper ? 'text-[#5eead4]' : 'text-[#a5b4fc]'}>
                      {isHelper ? 'HELPER' : 'YOU'}
                    </span>
                    {isAnomaly && isHelper && (
                      <span className="text-[10px] bg-[#991b1b] text-white px-1.5 py-0.2 rounded-xs font-bold uppercase tracking-wider">
                        MEMORY SLIP
                      </span>
                    )}
                  </div>
                  <p className="whitespace-pre-wrap break-words leading-relaxed text-[13px]">
                    {entry.text}
                  </p>
                </div>
              );
            })}

            {sending && (
              <div className="flex items-center gap-2 text-[#5eead4] text-xs pt-1 p-2 bg-[#0f172a]/40 border-l-4 border-[#0d9488]">
                <span>HELPER is formulating response...</span>
                <span className="inline-block w-2.5 h-4 bg-[#22c55e] cursor-blink" />
              </div>
            )}
          </div>

          {/* Quick Prompts Bar */}
          <div className="relative z-20 pt-2 border-t border-[#1f2937] shrink-0">
            <div className="text-[11px] text-[#9ca3af] mb-1 font-sans font-medium">
              Suggested Investigator Questions (click to send):
            </div>
            <div className="flex flex-wrap gap-1.5">
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  disabled={busy || sending}
                  onClick={() => handleSubmit(prompt)}
                  className="px-2.5 py-1 bg-[#1e293b] text-[#5eead4] hover:bg-[#334155] border border-[#475569] hover:border-[#5eead4] text-xs rounded-xs transition-colors cursor-pointer disabled:opacity-50 font-sans"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Investigator Command Bus / Chat Input Area */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit(message);
        }}
        className="p-2 bg-[#c0c0c0] border-t border-[#808080] flex flex-col gap-1.5 shrink-0"
      >
        <div className="flex items-center justify-between text-xs text-[#374151] font-sans font-bold">
          <label htmlFor="chat-message" className="cursor-pointer">
            Message HELPER:
          </label>
          <span className="font-mono text-[11px] text-[#6b7280]">
            {message.length} / 500 characters · Press Enter to send, Shift+Enter for new line
          </span>
        </div>

        <div className="flex gap-2">
          <textarea
            id="chat-message"
            rows={2}
            maxLength={500}
            value={message}
            disabled={sending}
            placeholder="Type your question or statement to HELPER..."
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
                e.preventDefault();
                handleSubmit(message);
              }
            }}
            className="flex-1 bg-white text-black p-2 font-mono text-[13px] w98-bevel-sunken focus:outline-none focus:ring-2 focus:ring-[#008080] resize-none leading-relaxed"
          />

          <button
            type="submit"
            disabled={busy || sending || !message.trim()}
            className="px-5 bg-[#c0c0c0] w98-btn text-xs font-bold text-[#006565] flex flex-col items-center justify-center gap-1 min-w-[80px] cursor-pointer"
          >
            <RetroIcon name="terminal" size={16} />
            <span>SEND</span>
          </button>
        </div>
      </form>

      {/* Window Status Bar */}
      <footer role="status" className="h-6 bg-[#c0c0c0] px-3 border-t border-[#808080] flex items-center justify-between text-xs text-[#374151] select-none font-mono">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 font-bold text-[#006565]">
            <RetroIcon name="check" size={12} />
            DAEMON READY
          </span>
          <span className="border-l border-[#808080] pl-2">PORT 8000</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[#6b7280]">{status}</span>
        </div>
      </footer>
    </div>
  );
};
