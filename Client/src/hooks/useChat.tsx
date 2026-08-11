import { useCallback, useEffect, useRef, useState } from 'react';
import {
  checkBackendHealth,
  getConversationMessages,
  sendChatMessage,
  ApiError,
} from '../api';
import type { ChatMessage } from '../types/chat';

function makeId(): string {
  return crypto.randomUUID();
}

const WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome',
  role: 'assistant',
  content:
    "Hi, I'm your stock market assistant. Ask me about a live price, fundamentals, recent news, or ask me to compare two tickers — or just ask a general market question.",
  createdAt: Date.now(),
};

interface UseChatOptions {
  activeThreadId: string | null;
  /** Called after the FIRST message of a brand-new conversation succeeds,
   *  so the sidebar can adopt the real thread_id + auto-generated title. */
  onConversationStarted: (threadId: string, firstUserMessage: string) => void;
  /** Called after every successful turn on an EXISTING conversation, so the
   *  sidebar can bump it to the top of the "most recent" ordering. */
  onConversationTouched: (threadId: string) => void;
}

export function useChat({
  activeThreadId,
  onConversationStarted,
  onConversationTouched,
}: UseChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [isSending, setIsSending] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isBackendOnline, setIsBackendOnline] = useState<boolean | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const loadedForThreadRef = useRef<string | null>(null);

  // Health polling — same as before.
  useEffect(() => {
    let cancelled = false;
    const check = async () => {
      const online = await checkBackendHealth();
      if (!cancelled) setIsBackendOnline(online);
    };
    check();
    const interval = setInterval(check, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  // Load history whenever the active conversation changes.
  useEffect(() => {
    if (!activeThreadId) {
      setMessages([WELCOME_MESSAGE]);
      loadedForThreadRef.current = null;
      return;
    }
    if (loadedForThreadRef.current === activeThreadId) return;

    let cancelled = false;
    setIsLoadingHistory(true);
    getConversationMessages(activeThreadId)
      .then((res) => {
        if (cancelled) return;
        loadedForThreadRef.current = activeThreadId;
        const loaded: ChatMessage[] = res.messages.map((m) => ({
          id: makeId(),
          role: m.role,
          content: m.content,
        }));
        setMessages(loaded.length > 0 ? loaded : [WELCOME_MESSAGE]);
      })
      .catch(() => {
        if (!cancelled) setMessages([WELCOME_MESSAGE]);
      })
      .finally(() => {
        if (!cancelled) setIsLoadingHistory(false);
      });

    return () => {
      cancelled = true;
    };
  }, [activeThreadId]);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isSending) return;

      const isNewConversation = !activeThreadId;

      const userMessage: ChatMessage = {
        id: makeId(),
        role: 'user',
        content: trimmed,
        createdAt: Date.now(),
      };
      const pendingReplyId = makeId();
      const pendingReply: ChatMessage = {
        id: pendingReplyId,
        role: 'assistant',
        content: '',
        createdAt: Date.now(),
        pending: true,
      };

      setMessages((prev) => [...prev, userMessage, pendingReply]);
      setIsSending(true);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        const response = await sendChatMessage(
          trimmed,
          activeThreadId ?? undefined,
          controller.signal
        );

        setMessages((prev) =>
          prev.map((m) =>
            m.id === pendingReplyId
              ? { ...m, content: response.reply, pending: false }
              : m
          )
        );

        loadedForThreadRef.current = response.thread_id;
        if (isNewConversation) {
          onConversationStarted(response.thread_id, trimmed);
        } else {
          onConversationTouched(response.thread_id);
        }
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : err instanceof DOMException && err.name === 'AbortError'
              ? 'Request cancelled.'
              : "Couldn't reach the agent backend. Is the FastAPI server running on port 8000?";
        setMessages((prev) =>
          prev.map((m) =>
            m.id === pendingReplyId
              ? { ...m, pending: false, error: message }
              : m
          )
        );
      } finally {
        setIsSending(false);
        abortRef.current = null;
      }
    },
    [activeThreadId, isSending, onConversationStarted, onConversationTouched]
  );

  const cancelSend = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return {
    messages,
    isSending,
    isLoadingHistory,
    isBackendOnline,
    sendMessage,
    cancelSend,
  };
}
