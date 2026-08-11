import { GoogleLogin, type CredentialResponse } from '@react-oauth/google';
import { TrendingUp } from 'lucide-react';
import { useState } from 'react';

interface LoginScreenProps {
  onLogin: (credential: string) => Promise<void>;
}

export function LoginScreen({ onLogin }: LoginScreenProps) {
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSuccess = async (response: CredentialResponse) => {
    if (!response.credential) {
      setError("Google didn't return a credential. Please try again.");
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      await onLogin(response.credential);
    } catch {
      setError('Sign-in failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen items-center justify-center bg-slate-50 px-4 dark:bg-surface-900">
      <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm dark:border-white/10 dark:bg-surface-800">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-accent to-accent-muted shadow-lg shadow-accent/20">
          <TrendingUp className="h-6 w-6 text-surface-900" strokeWidth={2.5} />
        </div>
        <h1 className="text-lg font-bold text-slate-900 dark:text-white">
          StockSense AI
        </h1>
        <p className="mt-1.5 mb-6 text-sm text-slate-500 dark:text-slate-400">
          Sign in to save and revisit your conversations.
        </p>

        <div className="flex justify-center">
          {isLoading ? (
            <div className="flex h-10 items-center text-sm text-slate-500 dark:text-slate-400">
              Signing in...
            </div>
          ) : (
            <GoogleLogin
              onSuccess={handleSuccess}
              onError={() =>
                setError('Google sign-in failed. Please try again.')
              }
              theme="outline"
              shape="pill"
            />
          )}
        </div>

        {error && (
          <p className="mt-4 text-xs text-rose-500 dark:text-rose-400">
            {error}
          </p>
        )}
      </div>
    </div>
  );
}
