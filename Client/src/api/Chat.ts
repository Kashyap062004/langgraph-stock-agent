import type {
  AuthUser,
  ChatRequestBody,
  ChatResponseBody,
  Conversation,
  MessagesResponseBody,
  TokenResponseBody,
} from '../types';

const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

let currentToken: string | null = null;
let onUnauthorized: (() => void) | null = null;

export function setAuthToken(token: string | null) {
  currentToken = token;
}

export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler;
}

function authHeaders(): Record<string, string> {
  return currentToken ? { Authorization: `Bearer ${currentToken}` } : {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    onUnauthorized?.();
  }
  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson?.detail) detail = errJson.detail;
    } catch {
      // response wasn't JSON — keep the generic message
    }
    throw new ApiError(detail, res.status);
  }
  return (await res.json()) as T;
}

export async function loginWithGoogle(
  credential: string
): Promise<TokenResponseBody> {
  const res = await fetch(`${API_BASE_URL}/auth/google`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential }),
  });
  return handleResponse<TokenResponseBody>(res);
}

export async function fetchCurrentUser(): Promise<AuthUser> {
  const res = await fetch(`${API_BASE_URL}/auth/me`, {
    headers: authHeaders(),
  });
  return handleResponse<AuthUser>(res);
}

export async function sendChatMessage(
  message: string,
  threadId: string | undefined,
  signal?: AbortSignal
): Promise<ChatResponseBody> {
  const body: ChatRequestBody = { message, thread_id: threadId };
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
    signal,
  });
  return handleResponse<ChatResponseBody>(res);
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { method: 'GET' });
    return res.ok;
  } catch {
    return false;
  }
}

export async function listConversations(): Promise<Conversation[]> {
  const res = await fetch(`${API_BASE_URL}/conversations`, {
    headers: authHeaders(),
  });
  return handleResponse<Conversation[]>(res);
}

export async function createConversation(): Promise<Conversation> {
  const res = await fetch(`${API_BASE_URL}/conversations`, {
    method: 'POST',
    headers: authHeaders(),
  });
  return handleResponse<Conversation>(res);
}

export async function getConversationMessages(
  threadId: string
): Promise<MessagesResponseBody> {
  const res = await fetch(
    `${API_BASE_URL}/conversations/${threadId}/messages`,
    {
      headers: authHeaders(),
    }
  );
  return handleResponse<MessagesResponseBody>(res);
}

export async function renameConversation(
  threadId: string,
  title: string
): Promise<Conversation> {
  const res = await fetch(`${API_BASE_URL}/conversations/${threadId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ title }),
  });
  return handleResponse<Conversation>(res);
}

export async function deleteConversation(threadId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/conversations/${threadId}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  await handleResponse<{ thread_id: string; deleted: boolean }>(res);
}

/**
 * Add these two functions to your existing chatApi.ts, alongside your
 * other API functions. They reuse the same authHeaders()/API_BASE_URL
 * already defined there — no new setup needed.
 */

/**
 * POST /reports/pdf — the backend returns raw PDF bytes with a
 * Content-Disposition header, not JSON. We read it as a Blob and trigger a
 * browser download via a temporary <a> element — this is the standard way
 * to turn a fetch() response into a native "Save As" download, since fetch
 * has no built-in "save this blob to disk" API.
 */
export async function downloadReportPdf(
  content: string,
  title: string
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/reports/pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ content, title }),
  });

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson?.detail) detail = errJson.detail;
    } catch {
      // not JSON — keep the generic message
    }
    throw new ApiError(detail, res.status);
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${title || 'report'}.pdf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url); // release the blob URL once the download has started
}

/** POST /reports/email — sends to the logged-in user's own verified email. */
export async function emailReport(
  content: string,
  title: string
): Promise<{ sent: boolean; to: string }> {
  const res = await fetch(`${API_BASE_URL}/reports/email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ content, title }),
  });

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson?.detail) detail = errJson.detail;
    } catch {
      // not JSON
    }
    throw new ApiError(detail, res.status);
  }

  return res.json();
}
