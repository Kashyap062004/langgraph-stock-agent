import { useState, type KeyboardEvent } from 'react';
import { Check, MessageSquarePlus, Pencil, Trash2, X } from 'lucide-react';
import type { Conversation } from '../types';

interface SidebarProps {
  conversations: Conversation[];
  activeThreadId: string | null;
  isLoading: boolean;
  onSelect: (threadId: string) => void;
  onNew: () => void;
  onRename: (threadId: string, title: string) => void;
  onDelete: (threadId: string) => void;
  isOpen: boolean;
}

function groupByRecency(conversations: Conversation[]) {
  const now = Date.now();
  const DAY = 86_400_000;
  const groups: { label: string; items: Conversation[] }[] = [
    { label: 'Today', items: [] },
    { label: 'Yesterday', items: [] },
    { label: 'Previous 7 days', items: [] },
    { label: 'Older', items: [] },
  ];

  for (const c of conversations) {
    const age = now - new Date(c.updated_at).getTime();
    if (age < DAY) groups[0].items.push(c);
    else if (age < 2 * DAY) groups[1].items.push(c);
    else if (age < 7 * DAY) groups[2].items.push(c);
    else groups[3].items.push(c);
  }

  return groups.filter((g) => g.items.length > 0);
}

export function Sidebar({
  conversations,
  activeThreadId,
  isLoading,
  onSelect,
  onNew,
  onRename,
  onDelete,
  isOpen,
}: SidebarProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const startEdit = (c: Conversation) => {
    setEditingId(c.thread_id);
    setEditValue(c.title);
  };

  const commitEdit = (threadId: string) => {
    const title = editValue.trim();
    if (title) onRename(threadId, title);
    setEditingId(null);
  };

  const handleEditKeyDown = (
    e: KeyboardEvent<HTMLInputElement>,
    threadId: string
  ) => {
    if (e.key === 'Enter') commitEdit(threadId);
    if (e.key === 'Escape') setEditingId(null);
  };

  const groups = groupByRecency(conversations);

  return (
    <aside
      className={`flex h-full shrink-0 flex-col overflow-hidden border-r border-slate-200 bg-slate-50 transition-all duration-200 dark:border-white/5 dark:bg-surface-800/60 ${
        isOpen ? 'w-72' : 'w-0 border-r-0'
      }`}
    >
      <div className="flex w-72 flex-col h-full">
        <div className="p-3">
          <button
            onClick={onNew}
            className="flex w-full items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-medium text-slate-700 shadow-sm transition hover:border-accent/40 hover:text-accent-muted dark:border-white/10 dark:bg-white/5 dark:text-slate-200 dark:shadow-none dark:hover:text-accent"
          >
            <MessageSquarePlus className="h-4 w-4" />
            New chat
          </button>
        </div>

        <div className="chat-scroll flex-1 overflow-y-auto px-2 pb-3">
          {isLoading && (
            <p className="px-2 py-4 text-xs text-slate-400 dark:text-slate-500">
              Loading conversations...
            </p>
          )}

          {!isLoading && conversations.length === 0 && (
            <p className="px-2 py-4 text-xs text-slate-400 dark:text-slate-500">
              No conversations yet — start one above.
            </p>
          )}

          {groups.map((group) => (
            <div key={group.label} className="mb-3">
              <h3 className="px-2 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400 dark:text-slate-500">
                {group.label}
              </h3>
              <div className="flex flex-col gap-0.5">
                {group.items.map((c) => {
                  const isActive = c.thread_id === activeThreadId;
                  const isEditing = editingId === c.thread_id;
                  const isConfirmingDelete = confirmDeleteId === c.thread_id;

                  return (
                    <div
                      key={c.thread_id}
                      className={`group relative flex items-center gap-1 rounded-lg px-2 py-2 text-sm transition ${
                        isActive
                          ? 'bg-accent/15 text-accent-muted dark:text-accent'
                          : 'text-slate-600 hover:bg-slate-200/60 dark:text-slate-300 dark:hover:bg-white/5'
                      }`}
                    >
                      {isEditing ? (
                        <>
                          <input
                            autoFocus
                            value={editValue}
                            onChange={(e) => setEditValue(e.target.value)}
                            onKeyDown={(e) => handleEditKeyDown(e, c.thread_id)}
                            onBlur={() => commitEdit(c.thread_id)}
                            className="min-w-0 flex-1 rounded-md border border-accent/40 bg-white px-1.5 py-0.5 text-sm text-slate-900 focus:outline-none dark:bg-surface-900 dark:text-slate-100"
                          />
                          <button
                            onClick={() => commitEdit(c.thread_id)}
                            className="shrink-0 rounded p-1 text-emerald-600 hover:bg-emerald-500/10 dark:text-emerald-400"
                            title="Save"
                          >
                            <Check className="h-3.5 w-3.5" />
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="shrink-0 rounded p-1 text-slate-500 hover:bg-slate-500/10"
                            title="Cancel"
                          >
                            <X className="h-3.5 w-3.5" />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => onSelect(c.thread_id)}
                            className="min-w-0 flex-1 truncate text-left"
                            title={c.title}
                          >
                            {c.title}
                          </button>

                          {isConfirmingDelete ? (
                            <div className="flex shrink-0 items-center gap-1">
                              <button
                                onClick={() => {
                                  onDelete(c.thread_id);
                                  setConfirmDeleteId(null);
                                }}
                                className="rounded px-1.5 py-0.5 text-[11px] font-medium text-rose-600 hover:bg-rose-500/10 dark:text-rose-400"
                              >
                                Delete
                              </button>
                              <button
                                onClick={() => setConfirmDeleteId(null)}
                                className="rounded p-1 text-slate-500 hover:bg-slate-500/10"
                              >
                                <X className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          ) : (
                            <div className="hidden shrink-0 items-center gap-0.5 group-hover:flex">
                              <button
                                onClick={() => startEdit(c)}
                                className="rounded p-1 text-slate-400 hover:bg-slate-500/10 hover:text-slate-700 dark:hover:text-slate-200"
                                title="Rename"
                              >
                                <Pencil className="h-3.5 w-3.5" />
                              </button>
                              <button
                                onClick={() => setConfirmDeleteId(c.thread_id)}
                                className="rounded p-1 text-slate-400 hover:bg-rose-500/10 hover:text-rose-500"
                                title="Delete"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
