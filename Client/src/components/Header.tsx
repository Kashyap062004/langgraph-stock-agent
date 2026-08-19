import {
  TrendingUp,
  RotateCcw,
  Circle,
  PanelLeft,
  PanelRight,
  LogOut,
} from 'lucide-react';
import { ThemeToggle } from './Themetoggle';
import type { Theme } from '../hooks';
import type { AuthUser } from '../types';

interface HeaderProps {
  isBackendOnline: boolean | null;
  onNewConversation: () => void;
  theme: Theme;
  onToggleTheme: () => void;
  onToggleSidebar: () => void;
  onToggleInsights: () => void;
  user: AuthUser;
  onLogout: () => void;
}

export function Header({
  isBackendOnline,
  onNewConversation,
  theme,
  onToggleTheme,
  onToggleSidebar,
  onToggleInsights,
  user,
  onLogout,
}: HeaderProps) {
  const statusColor =
    isBackendOnline === null
      ? 'text-slate-400 dark:text-slate-500'
      : isBackendOnline
        ? 'text-emerald-500 dark:text-emerald-400'
        : 'text-rose-500';

  const statusLabel =
    isBackendOnline === null
      ? 'Checking...'
      : isBackendOnline
        ? 'Agent online'
        : 'Agent offline';

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white/80 px-5 py-4 backdrop-blur dark:border-white/5 dark:bg-surface-900/80">
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar}
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-white"
          title="Toggle conversation history"
        >
          <PanelLeft className="h-4 w-4" />
        </button>
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-accent-muted shadow-lg shadow-accent/20">
          <TrendingUp className="h-5 w-5 text-surface-900" strokeWidth={2.5} />
        </div>
        <div>
          <h1 className="text-sm font-bold leading-none text-slate-900 dark:text-white">
            StockSense AI
          </h1>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
            Live market data · fundamentals · news
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden items-center gap-1.5 text-xs font-medium sm:flex">
          <Circle className={`h-2 w-2 fill-current ${statusColor}`} />
          <span className={statusColor}>{statusLabel}</span>
        </div>
        <button
          onClick={onNewConversation}
          className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-slate-300 hover:bg-slate-100 hover:text-slate-900 dark:border-white/10 dark:text-slate-300 dark:hover:border-white/20 dark:hover:bg-white/5 dark:hover:text-white"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          <span className="hidden sm:inline">New chat</span>
        </button>
        <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        <button
          onClick={onToggleInsights}
          title="Documents & watchlist"
          className="flex h-8 w-8 items-center justify-center rounded-lg text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-white"
        >
          <PanelRight className="h-4 w-4" />
        </button>
        <div className="ml-1 flex items-center gap-2 border-l border-slate-200 pl-3 dark:border-white/10">
          {user.picture ? (
            <img
              src={user.picture}
              alt={user.name}
              className="h-7 w-7 rounded-full"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-accent/15 text-xs font-semibold text-accent-muted dark:text-accent">
              {user.name.charAt(0).toUpperCase()}
            </div>
          )}
          <span className="hidden text-xs font-medium text-slate-600 dark:text-slate-300 md:inline">
            {user.name}
          </span>
          <button
            onClick={onLogout}
            title="Sign out"
            className="flex h-7 w-7 items-center justify-center rounded-lg text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-white/5 dark:hover:text-white"
          >
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </header>
  );
}
