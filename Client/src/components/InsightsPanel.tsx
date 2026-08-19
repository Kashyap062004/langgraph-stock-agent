import { useState } from 'react';
import { FileText, Star, X } from 'lucide-react';
import { DocumentsPanel } from './DocumentsPanel';
import { WatchlistPanel } from './WatchlistPanel';

type Tab = 'documents' | 'watchlist';

interface InsightsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function InsightsPanel({ isOpen, onClose }: InsightsPanelProps) {
  const [tab, setTab] = useState<Tab>('documents');

  return (
    <aside
      className={`flex h-full shrink-0 flex-col overflow-hidden border-l border-slate-200 bg-slate-50 transition-all duration-200 dark:border-white/5 dark:bg-surface-800/60 ${
        isOpen ? 'w-80' : 'w-0 border-l-0'
      }`}
    >
      <div className="flex h-full w-80 flex-col">
        <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2.5 dark:border-white/10">
          <div className="flex gap-1">
            <button
              onClick={() => setTab('documents')}
              className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition ${
                tab === 'documents'
                  ? 'bg-accent/15 text-accent-muted dark:text-accent'
                  : 'text-slate-500 hover:bg-slate-200/60 dark:text-slate-400 dark:hover:bg-white/5'
              }`}
            >
              <FileText className="h-3.5 w-3.5" />
              Documents
            </button>
            <button
              onClick={() => setTab('watchlist')}
              className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition ${
                tab === 'watchlist'
                  ? 'bg-accent/15 text-accent-muted dark:text-accent'
                  : 'text-slate-500 hover:bg-slate-200/60 dark:text-slate-400 dark:hover:bg-white/5'
              }`}
            >
              <Star className="h-3.5 w-3.5" />
              Watchlist
            </button>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-200/60 hover:text-slate-600 dark:hover:bg-white/5 dark:hover:text-slate-200"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-hidden">
          {tab === 'documents' ? <DocumentsPanel /> : <WatchlistPanel />}
        </div>
      </div>
    </aside>
  );
}
