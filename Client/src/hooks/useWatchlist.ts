import { useCallback, useEffect, useState } from 'react';
import {
  addToWatchlist,
  getWatchlist,
  removeFromWatchlist,
} from '../api';

export function useWatchlist() {
  const [tickers, setTickers] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getWatchlist()
      .then((res) => {
        if (!cancelled) setTickers(res.tickers);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const add = useCallback(async (ticker: string) => {
    const trimmed = ticker.trim().toUpperCase();
    if (!trimmed) return;
    setError(null);
    try {
      const res = await addToWatchlist(trimmed);
      setTickers(res.tickers);
    } catch {
      setError(`Couldn't add ${trimmed}.`);
    }
  }, []);

  const remove = useCallback(async (ticker: string) => {
    const res = await removeFromWatchlist(ticker);
    setTickers(res.tickers);
  }, []);

  return { tickers, isLoading, error, add, remove };
}
