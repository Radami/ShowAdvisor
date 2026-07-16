import { useCallback, useRef, useState } from 'react';
import { useFocusEffect } from '@react-navigation/native';
import { useAuth } from './auth';
import { EntityKind, SubscriptionStatus } from './api';

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

  // `setData` is exposed so callers can apply optimistic edits directly to the
  // fetched data; the next focus refetch overwrites them with server truth.
  return { data, error, reload: load, setData };
}

/** A detail payload that carries a subscription the user can toggle. */
interface Subscribable {
  subscription: { status: SubscriptionStatus } | null;
}

// Identifies the subscription control for in-flight de-duping (below).
const SUBSCRIPTION_KEY = 'subscription';

/**
 * Detail-screen data with optimistic writes, shared by the Show and Movie
 * detail screens. `mutate` applies an optimistic edit straight onto the
 * fetched data, runs the write, and refetches server truth if it fails;
 * `setSubscription` maps a target subscription onto the right
 * subscribe/unsubscribe/patch call.
 */
export function useOptimisticDetail<T extends Subscribable>(
  entity: EntityKind,
  id: number,
  fetcher: () => Promise<T>,
) {
  const { api } = useAuth();
  const { data, error, reload, setData } = useFocusedFetch(fetcher);

  // Targets with a write in flight, keyed per control (a single episode, a
  // season, the subscription…). This de-dupes a double-tap on one target
  // while still letting different targets update at the same time.
  const inFlight = useRef(new Set<string>());

  const mutate = async (
    key: string,
    optimistic: (current: T) => T,
    call: () => Promise<unknown>,
  ) => {
    if (!data || inFlight.current.has(key)) {
      return;
    }

    inFlight.current.add(key);

    // Apply the edit functionally so concurrent optimistic updates compose
    // instead of overwriting each other.
    setData(current => (current ? optimistic(current) : current));

    try {
      await call();
    } catch {
      reload(); // write failed — snap back to server truth
    } finally {
      inFlight.current.delete(key);
    }
  };

  // Translate the desired subscription state into the matching API verb.
  const setSubscription = (subscription: T['subscription']) =>
    mutate(
      SUBSCRIPTION_KEY,
      current => ({ ...current, subscription }),
      () => {
        if (!subscription) {
          return api.unsubscribe(entity, id);
        }

        if (!data?.subscription) {
          return api.subscribe(entity, id);
        }

        return api.setSubscriptionStatus(entity, id, subscription.status);
      },
    );

  return { data, error, mutate, setSubscription };
}

export function formatDate(value: string | null | undefined): string | null {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  return isNaN(date.getTime()) ? null : date.toDateString().slice(4);
}
