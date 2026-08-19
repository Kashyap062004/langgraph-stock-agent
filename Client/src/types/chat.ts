
export type MessageRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt?: number;
  pending?: boolean;
  error?: string;
}

export interface ChatRequestBody {
  message: string;
  thread_id?: string;
}

export interface ChatResponseBody {
  reply: string;
  thread_id: string;
}

export interface Conversation {
  thread_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface HistoryMessage {
  role: MessageRole;
  content: string;
}

export interface MessagesResponseBody {
  thread_id: string;
  messages: HistoryMessage[];
}

export interface AuthUser {
  sub: string;
  email: string;
  name: string;
  picture: string | null;
}

export interface TokenResponseBody {
  access_token: string;
  user: AuthUser;
}

export interface StockDocument {
  doc_id: string;
  filename: string;
  ticker: string | null;
  chunk_count: number;
  uploaded_at: string;
}

export interface WatchlistResponse {
  tickers: string[];
}
