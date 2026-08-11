import ReactMarkdown from 'react-markdown';
import { AlertCircle, Bot, User } from 'lucide-react';
import type { ChatMessage } from '../types/chat';
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

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex w-full animate-fade-in gap-3 ${
        isUser ? 'flex-row-reverse' : 'flex-row'
      }`}
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
        {!message.pending && message.createdAt !== undefined && (
          <span className="mt-1 px-1 text-[11px] text-slate-400 dark:text-slate-500">
            {formatTime(message.createdAt)}
          </span>
        )}
      </div>
    </div>
  );
}
