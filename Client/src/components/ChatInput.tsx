import { useRef, useState, type KeyboardEvent } from 'react';
import { Send, Square } from 'lucide-react';

interface ChatInputProps {
  onSend: (text: string) => void;
  onCancel: () => void;
  isSending: boolean;
  disabled?: boolean;
}

export function ChatInput({
  onSend,
  onCancel,
  isSending,
  disabled,
}: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  const handleSend = () => {
    if (!value.trim() || isSending) return;
    onSend(value);
    setValue('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  return (
    <div className="border-t border-slate-200 bg-white/80 px-4 py-4 backdrop-blur dark:border-white/5 dark:bg-surface-900/80 sm:px-8">
      <div className="mx-auto flex max-w-2xl items-end gap-2 rounded-2xl border border-slate-200 bg-slate-50 p-2 shadow-sm transition focus-within:border-accent/50 dark:border-white/10 dark:bg-surface-800 dark:shadow-lg dark:focus-within:border-accent/40">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          rows={1}
          disabled={disabled}
          placeholder="Ask about a ticker, fundamentals, news, or a market concept..."
          className="max-h-40 flex-1 resize-none bg-transparent px-2 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none disabled:opacity-50 dark:text-slate-100 dark:placeholder:text-slate-500"
        />
        {isSending ? (
          <button
            onClick={onCancel}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-slate-200 text-slate-600 transition hover:bg-slate-300 dark:bg-white/10 dark:text-slate-300 dark:hover:bg-white/20"
            title="Stop"
          >
            <Square className="h-4 w-4" />
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!value.trim() || disabled}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent text-surface-900 transition hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-30"
            title="Send"
          >
            <Send className="h-4 w-4" />
          </button>
        )}
      </div>
      <p className="mx-auto mt-2 max-w-2xl text-center text-[11px] text-slate-400 dark:text-slate-600">
        StockSense AI can make mistakes. Verify important figures before trading
        on them.
      </p>
    </div>
  );
}
