const THREAD_ID_KEY = 'stock-agent-thread-id';

export function getOrCreateThreadId(): string {
  const existing = localStorage.getItem(THREAD_ID_KEY);
  if (existing) return existing;

  const id = crypto.randomUUID();
  localStorage.setItem(THREAD_ID_KEY, id);
  return id;
}

export function resetThreadId(): string {
  const id = crypto.randomUUID();
  localStorage.setItem(THREAD_ID_KEY, id);
  return id;
}
