import { useCallback, useEffect, useState } from 'react';
import {
  createConversation,
  deleteConversation,
  listConversations,
  renameConversation,
} from '../api';
import type { Conversation } from '../types/chat';

const ACTIVE_THREAD_KEY = 'stock-agent-active-thread';

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeThreadId, setActiveThreadIdState] = useState<string | null>(() =>
    localStorage.getItem(ACTIVE_THREAD_KEY)
  );
  const [isLoading, setIsLoading] = useState(true);

  const setActiveThreadId = useCallback((threadId: string | null) => {
    setActiveThreadIdState(threadId);
    if (threadId) localStorage.setItem(ACTIVE_THREAD_KEY, threadId);
    else localStorage.removeItem(ACTIVE_THREAD_KEY);
  }, []);

  const refresh = useCallback(async () => {
    try {
      const list = await listConversations();
      setConversations(list);
      return list;
    } catch {
      // Backend offline — leave the existing list as-is rather than wiping
      // the sidebar; useChat's health check already surfaces the outage.
      return conversations;
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }
  }, []);

  // Initial load: fetch the list, and if the previously active thread no
  // longer exists (e.g. deleted from another tab), fall back to the most
  // recent conversation, or null (empty state) if there are none at all.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const list = await refresh();
      if (cancelled) return;
      setActiveThreadIdState((current) => {
        const stillExists =
          current && list.some((c) => c.thread_id === current);
        if (stillExists) return current;
        const fallback = list[0]?.thread_id ?? null;
        if (fallback) localStorage.setItem(ACTIVE_THREAD_KEY, fallback);
        else localStorage.removeItem(ACTIVE_THREAD_KEY);
        return fallback;
      });
      setIsLoading(false);
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startNewConversation = useCallback(async () => {
    const conv = await createConversation();
    setConversations((prev) => [conv, ...prev]);
    setActiveThreadId(conv.thread_id);
    return conv.thread_id;
  }, [setActiveThreadId]);

  const removeConversation = useCallback(
    async (threadId: string) => {
      await deleteConversation(threadId);
      setConversations((prev) => {
        const next = prev.filter((c) => c.thread_id !== threadId);
        if (activeThreadId === threadId) {
          setActiveThreadId(next[0]?.thread_id ?? null);
        }
        return next;
      });
    },
    [activeThreadId, setActiveThreadId]
  );

  const renameConversationTitle = useCallback(
    async (threadId: string, title: string) => {
      const updated = await renameConversation(threadId, title);
      setConversations((prev) =>
        prev.map((c) => (c.thread_id === threadId ? updated : c))
      );
    },
    []
  );

  /**
   * Called after a successful /chat turn: keeps the sidebar in sync without
   * a full re-fetch — bumps updated_at (re-sorting to the top, matching the
   * backend's ORDER BY updated_at DESC) and, for a brand-new conversation
   * whose title the backend just auto-generated, adopts that real title in
   * place of the "New conversation" placeholder.
   */
  const applyOptimisticTouch = useCallback(
    (threadId: string, newTitle?: string) => {
      setConversations((prev) => {
        const existing = prev.find((c) => c.thread_id === threadId);
        const now = new Date().toISOString();
        if (!existing) {
          // Conversation created server-side via a threadId-less /chat call
          // — not yet in local state at all. Insert it at the top.
          return [
            {
              thread_id: threadId,
              title: newTitle ?? 'New conversation',
              created_at: now,
              updated_at: now,
            },
            ...prev,
          ];
        }
        const touched: Conversation = {
          ...existing,
          title: newTitle ?? existing.title,
          updated_at: now,
        };
        return [touched, ...prev.filter((c) => c.thread_id !== threadId)];
      });
    },
    []
  );

  return {
    conversations,
    activeThreadId,
    isLoading,
    setActiveThreadId,
    startNewConversation,
    removeConversation,
    renameConversationTitle,
    applyOptimisticTouch,
    refresh,
  };
}
