import { useCallback, useState } from 'react';
import { Header } from './components/Header';
import { ChatWindow } from './components/ChatWindow';
import { ChatInput } from './components/ChatInput';
import { Sidebar } from './components/Sidebar';
import { LoginScreen } from './components/Loginscreen';
import { useChat } from './hooks/useChat';
import { useTheme } from './hooks/useTheme';
import { useConversations } from './hooks';
import { useAuth } from './hooks/useauth';

function AuthenticatedApp({
  user,
  onLogout,
}: {
  user: NonNullable<ReturnType<typeof useAuth>['user']>;
  onLogout: () => void;
}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const { theme, toggleTheme } = useTheme();

  const {
    conversations,
    activeThreadId,
    isLoading: isLoadingConversations,
    setActiveThreadId,
    removeConversation,
    renameConversationTitle,
    applyOptimisticTouch,
  } = useConversations();

  const handleConversationStarted = useCallback(
    (threadId: string) => {
      applyOptimisticTouch(threadId);
      setActiveThreadId(threadId);
    },
    [applyOptimisticTouch, setActiveThreadId]
  );

  const handleConversationTouched = useCallback(
    (threadId: string) => {
      applyOptimisticTouch(threadId);
    },
    [applyOptimisticTouch]
  );

  const { messages, isSending, isBackendOnline, sendMessage, cancelSend } =
    useChat({
      activeThreadId,
      onConversationStarted: handleConversationStarted,
      onConversationTouched: handleConversationTouched,
    });

  const handleNewChat = useCallback(() => {
    setActiveThreadId(null);
  }, [setActiveThreadId]);

  return (
    <div className="flex h-screen w-screen bg-white transition-colors duration-200 dark:bg-surface-900">
      <Sidebar
        conversations={conversations}
        activeThreadId={activeThreadId}
        isLoading={isLoadingConversations}
        onSelect={setActiveThreadId}
        onNew={handleNewChat}
        onRename={renameConversationTitle}
        onDelete={removeConversation}
        isOpen={isSidebarOpen}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header
          isBackendOnline={isBackendOnline}
          onNewConversation={handleNewChat}
          theme={theme}
          onToggleTheme={toggleTheme}
          onToggleSidebar={() => setIsSidebarOpen((v) => !v)}
          user={user}
          onLogout={onLogout}
        />
        <ChatWindow messages={messages} onSuggestionClick={sendMessage} />
        <ChatInput
          onSend={sendMessage}
          onCancel={cancelSend}
          isSending={isSending}
          disabled={isBackendOnline === false}
        />
      </div>
    </div>
  );
}

export default function App() {
  const {
    user,
    isAuthenticated,
    isCheckingSession,
    loginWithGoogleCredential,
    logout,
  } = useAuth();

  if (isCheckingSession) {
    // Validating a stored token against GET /auth/me — avoid flashing the
    // login screen for a session that's actually still valid.
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-white dark:bg-surface-900">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-slate-300 border-t-accent dark:border-white/10" />
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return <LoginScreen onLogin={loginWithGoogleCredential} />;
  }

  return <AuthenticatedApp user={user} onLogout={logout} />;
}
