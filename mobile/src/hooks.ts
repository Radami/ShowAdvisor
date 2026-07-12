import { useCallback, useState } from 'react';
import { useFocusEffect } from '@react-navigation/native';

/**
 * Fetch data every time the screen gains focus — marking something watched
 * on a detail screen must be reflected when the user lands back on a list
 * tab, without any client-side cache to invalidate.
 */
export function useFocusedFetch<T>(fetcher: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    let cancelled = false;
    fetcher()
      .then(result => {
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      })
      .catch(e => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : String(e));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [fetcher]);

  useFocusEffect(load);

  return { data, error, reload: load };
}

export function formatDate(value: string | null | undefined): string | null {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  return isNaN(date.getTime()) ? null : date.toDateString().slice(4);
}
