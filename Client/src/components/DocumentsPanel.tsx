import { useRef, useState } from 'react';
import { FileText, Loader2, Trash2, Upload } from 'lucide-react';
import { useDocuments } from '../hooks';

export function DocumentsPanel() {
  const { documents, isLoading, isUploading, uploadError, upload, remove } =
    useDocuments();
  const [ticker, setTicker] = useState('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await upload(file, ticker.trim() || undefined);
      setTicker('');
    } catch {
      // uploadError from the hook is already shown below
    } finally {
      e.target.value = '';
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-slate-200 p-3 dark:border-white/10">
        <input
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="Ticker (optional, e.g. AAPL)"
          className="mb-2 w-full rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs text-slate-900 placeholder:text-slate-400 focus:border-accent/50 focus:outline-none dark:border-white/10 dark:bg-surface-900 dark:text-slate-100 dark:placeholder:text-slate-500"
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-slate-300 px-3 py-2.5 text-xs font-medium text-slate-500 transition hover:border-accent/40 hover:text-accent-muted disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/15 dark:text-slate-400 dark:hover:text-accent"
        >
          {isUploading ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="h-3.5 w-3.5" />
              Upload PDF, TXT, or MD
            </>
          )}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md"
          onChange={handleFileChange}
          className="hidden"
        />
        {uploadError && (
          <p className="mt-2 text-[11px] text-rose-500 dark:text-rose-400">
            {uploadError}
          </p>
        )}
      </div>

      <div className="chat-scroll flex-1 overflow-y-auto p-2">
        {isLoading && (
          <p className="px-2 py-4 text-xs text-slate-400 dark:text-slate-500">
            Loading...
          </p>
        )}
        {!isLoading && documents.length === 0 && (
          <p className="px-2 py-4 text-xs text-slate-400 dark:text-slate-500">
            No documents uploaded yet. Upload a 10-K, 10-Q, or research note to
            let the agent reference it in chat.
          </p>
        )}
        {documents.map((doc) => (
          <div
            key={doc.doc_id}
            className="group flex items-start gap-2 rounded-lg px-2 py-2 text-sm hover:bg-slate-100 dark:hover:bg-white/5"
          >
            <FileText className="mt-0.5 h-4 w-4 shrink-0 text-slate-400 dark:text-slate-500" />
            <div className="min-w-0 flex-1">
              <p
                className="truncate text-slate-700 dark:text-slate-200"
                title={doc.filename}
              >
                {doc.filename}
              </p>
              <p className="text-[11px] text-slate-400 dark:text-slate-500">
                {doc.ticker ? `${doc.ticker} · ` : ''}
                {doc.chunk_count} chunks
              </p>
            </div>
            <button
              onClick={() => remove(doc.doc_id)}
              className="hidden shrink-0 rounded p-1 text-slate-400 hover:bg-rose-500/10 hover:text-rose-500 group-hover:block"
              title="Delete"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
