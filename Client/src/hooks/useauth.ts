import { useCallback, useEffect, useState } from 'react';
import {
  fetchCurrentUser,
  loginWithGoogle,
  setAuthToken,
  setUnauthorizedHandler,
} from '../api';
import type { AuthUser } from '../types/chat';

const TOKEN_KEY = 'stock-agent-session-token';

export function useAuth() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isCheckingSession, setIsCheckingSession] = useState<boolean>(
    () => localStorage.getItem(TOKEN_KEY) !== null
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setAuthToken(null);
    setUser(null);
  }, []);

 

  useEffect(() => {
    setUnauthorizedHandler(logout);
    return () => setUnauthorizedHandler(null);
  }, [logout]);

 
  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (!stored) {
      setIsCheckingSession(false);
      return;
    }
    setAuthToken(stored);
    fetchCurrentUser()
      .then((u) => setUser(u))
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setAuthToken(null);
      })
      .finally(() => setIsCheckingSession(false));
  }, []);


  const loginWithGoogleCredential = useCallback(async (credential: string) => {
    const { access_token, user: loggedInUser } =
      await loginWithGoogle(credential);
    localStorage.setItem(TOKEN_KEY, access_token);
    setAuthToken(access_token);
    setUser(loggedInUser);
  }, []);

  return {
    user,
    isAuthenticated: user !== null,
    isCheckingSession,
    loginWithGoogleCredential,
    logout,
  };
}
