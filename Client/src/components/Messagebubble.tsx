import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { AlertCircle, Bot, Download, Loader2, Mail, User } from 'lucide-react';
import type { ChatMessage } from '../types/chat';
import { downloadReportPdf, emailReport, ApiError } from '../api';
import { TypingIndicator } from './Typingindicator';

interface MessageBubbleProps {
  message: ChatMessage;
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });
}

function deriveReportTitle(content: string): string {
  const headerMatch = content.match(/^#{1,2}\s+(.+)$/m);
  if (headerMatch) return headerMatch[1].trim();
  const firstLine =
    content.split('\n').find((l) => l.trim().length > 0) ?? 'Stock Report';
  return firstLine.length > 60
    ? firstLine.slice(0, 60).trim() + '…'
    : firstLine.trim();
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [isDownloading, setIsDownloading] = useState(false);
  const [emailState, setEmailState] = useState<
    'idle' | 'sending' | 'sent' | 'error'
  >('idle');
  const [actionError, setActionError] = useState<string | null>(null);

  
  const canExportReport =
    !isUser && !message.pending && !message.error && message.id !== 'welcome';

  const handleDownload = async () => {
    setActionError(null);
    setIsDownloading(true);
    try {
      await downloadReportPdf(
        message.content,
        deriveReportTitle(message.content)
      );
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : 'Download failed.'
      );
    } finally {
      setIsDownloading(false);
    }
  };

  const handleEmail = async () => {
    setActionError(null);
    setEmailState('sending');
    try {
      await emailReport(message.content, deriveReportTitle(message.content));
      setEmailState('sent');
      setTimeout(() => setEmailState('idle'), 3000); 
    } catch (err) {
      setEmailState('error');
      setActionError(err instanceof ApiError ? err.message : 'Email failed.');
    }
  };

  return (
    <div
      className={`flex w-full animate-fade-in gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser
            ? 'bg-accent/15 text-accent-muted dark:text-accent'
            : 'bg-slate-200 text-slate-500 dark:bg-white/5 dark:text-slate-300'
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div
        className={`flex max-w-[75%] flex-col ${isUser ? 'items-end' : 'items-start'}`}
      >
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm ${
            isUser
              ? 'rounded-tr-sm bg-accent font-medium text-surface-900'
              : message.error
                ? 'rounded-tl-sm border border-rose-300 bg-rose-50 text-rose-600 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300'
                : 'rounded-tl-sm border border-slate-200 bg-white text-slate-800 dark:border-white/5 dark:bg-surface-800 dark:text-slate-100'
          }`}
        >
          {message.pending ? (
            <TypingIndicator />
          ) : message.error ? (
            <div className="flex items-start gap-2">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>{message.error}</span>
            </div>
          ) : isUser ? (
            <span className="whitespace-pre-wrap">{message.content}</span>
          ) : (
            <div className="md-content">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {canExportReport && (
          <div className="mt-1.5 flex items-center gap-1">
            <button
              onClick={handleDownload}
              disabled={isDownloading}
              title="Download as PDF"
              className="flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 disabled:opacity-50 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-200"
            >
              {isDownloading ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Download className="h-3 w-3" />
              )}
              Download report
            </button>
            <button
              onClick={handleEmail}
              disabled={emailState === 'sending'}
              title="Email as PDF"
              className="flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-700 disabled:opacity-50 dark:text-slate-400 dark:hover:bg-white/5 dark:hover:text-slate-200"
            >
              {emailState === 'sending' ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Mail className="h-3 w-3" />
              )}
              {emailState === 'sent' ? 'Sent!' : 'Email report'}
            </button>
          </div>
        )}

        {actionError && (
          <p className="mt-1 max-w-[240px] text-[11px] text-rose-500 dark:text-rose-400">
            {actionError}
          </p>
        )}

        {!message.pending && message.createdAt !== undefined && (
          <span className="mt-1 px-1 text-[11px] text-slate-400 dark:text-slate-500">
            {formatTime(message.createdAt)}
          </span>
        )}
      </div>
    </div>
  );
}
