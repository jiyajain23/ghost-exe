import { useEffect, useRef, useState } from 'react';
export interface Exchange { speaker: 'HELPER' | 'YOU'; text: string }
export function Helper({ messages, busy, sending, onSend }: {
  messages: Exchange[]; busy: boolean; sending: boolean; onSend: (message: string, done: () => void) => void;
}) {
  const [message, setMessage] = useState(''); const history = useRef<HTMLDivElement>(null);
  useEffect(() => { if (history.current) history.current.scrollTop = history.current.scrollHeight; }, [messages, sending]);
  return <><div className="helper-profile"><div className="helper-face" aria-hidden="true">:)</div><div><strong>HELPER</strong><p>Archive indexing service</p><span><i /> Local · scripted dialogue</span></div></div>
    <div ref={history} className="chat-history" role="log" aria-label="HELPER conversation" tabIndex={0} aria-live="polite">
      {messages.map((entry, index) => <div className={`chat-entry ${entry.speaker === 'YOU' ? 'player' : ''}`} key={index}><strong>{entry.speaker}</strong><p>{entry.text}</p></div>)}
      {sending && <p className="typing">HELPER is replying…</p>}
    </div><form className="chat-form" onSubmit={event => { event.preventDefault(); if (message.trim() && !busy) onSend(message, () => setMessage('')); }}>
      <label htmlFor="chat-message">Message HELPER</label>
      <textarea id="chat-message" rows={3} maxLength={500} value={message} disabled={sending} placeholder="Ask about the archive…" onChange={event => setMessage(event.target.value)}
        onKeyDown={event => { if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
          event.preventDefault(); if (message.trim() && !busy) onSend(message, () => setMessage(''));
        } }} />
      <div className="chat-send"><small>{message.length}/500 · Shift+Enter for a new line</small><button type="submit" disabled={busy || !message.trim()}>Send</button></div>
    </form><footer className="window-status">Conversation text is not saved on disk.</footer></>;
}
