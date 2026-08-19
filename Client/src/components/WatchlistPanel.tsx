import { useState, type KeyboardEvent } from 'react';
import { Star, X } from 'lucide-react';
import { useWatchlist } from '../hooks';

export function WatchlistPanel() {
  const { tickers, isLoading, error, add, remove } = useWatchlist();
  const [input, setInput] = useState('');

  const handleAdd = async () => {
    if (!input.trim()) return;
    await add(input);
    setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleAdd();
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-200 p-3 dark:border-white/10">
        <div className="flex gap-1.5">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Add ticker (e.g. TSLA)"
            className="min-w-0 flex-1 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:border-accent/50 focus:outline-none dark:border-white/10 dark:bg-surface-900 dark:text-slate-100 dark:placeholder:text-slate-500"
          />
          <button
            onClick={handleAdd}
            className="shrink-0 rounded-lg bg-accent px-3 text-xs font-medium text-surface-900 transition hover:bg-accent/90"
          >
            Add
          </button>
        </div>
        {error && (
          <p className="mt-2 text-[11px] text-rose-500 dark:text-rose-400">
            {error}
          </p>
        )}
      </div>

      <div className="chat-scroll flex-1 overflow-y-auto p-2">
        {isLoading && (
          <p className="px-2 py-4 text-xs text-slate-400 dark:text-slate-500">
            Loading...
          </p>
        )}
        {!isLoading && tickers.length === 0 && (
          <p className="px-2 py-4 text-xs text-slate-400 dark:text-slate-500">
            No tickers saved yet. Add one above, then ask "how's my watchlist
            doing" in chat.
          </p>
        )}
        {tickers.map((t) => (
          <div
            key={t}
            className="group flex items-center gap-2 rounded-lg px-2 py-2 text-sm hover:bg-slate-100 dark:hover:bg-white/5"
          >
            <Star className="h-3.5 w-3.5 shrink-0 text-accent-muted dark:text-accent" />
            <span className="flex-1 font-medium text-slate-700 dark:text-slate-200">
              {t}
            </span>
            <button
              onClick={() => remove(t)}
              className="hidden shrink-0 rounded p-1 text-slate-400 hover:bg-rose-500/10 hover:text-rose-500 group-hover:block"
              title="Remove"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
