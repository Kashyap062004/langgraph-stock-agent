import { useEffect, useRef } from 'react';
import type { ChatMessage } from '../types/chat';
import { MessageBubble } from './Messagebubble';

const SUGGESTIONS = [
  "What's the current price of TSLA?",
  'Compare AAPL and MSFT fundamentals',
  'What is a P/E ratio?',
  'Any recent news on NVDA?',
];

interface ChatWindowProps {
  messages: ChatMessage[];
  onSuggestionClick: (text: string) => void;
}

export function ChatWindow({ messages, onSuggestionClick }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const showSuggestions = messages.length <= 1;

  return (
    <div className="chat-scroll flex-1 overflow-y-auto bg-slate-50 px-4 py-6 dark:bg-surface-900 sm:px-8">
      <div className="mx-auto flex max-w-2xl flex-col gap-5">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {showSuggestions && (
          <div className="ml-11 flex flex-wrap gap-2 animate-fade-in">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => onSuggestionClick(s)}
                className="rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs text-slate-600 shadow-sm transition hover:border-accent/40 hover:bg-accent/10 hover:text-accent-muted dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:shadow-none dark:hover:text-accent"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
