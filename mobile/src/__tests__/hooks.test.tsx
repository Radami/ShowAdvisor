/* eslint-env jest */
import React from 'react';
import { Text } from 'react-native';
import { act, render, waitFor } from '@testing-library/react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { AuthContext } from '../auth';
import { formatDate, useFocusedFetch, useOptimisticDetail } from '../hooks';
import { mockApi, MockApi } from './helpers/mockApi';
import { makeShowDetail } from './helpers/fixtures';

describe('formatDate', () => {
  it('returns null for empty or nullish input', () => {
    expect(formatDate(null)).toBeNull();
    expect(formatDate(undefined)).toBeNull();
    expect(formatDate('')).toBeNull();
  });

  it('returns null for an unparseable date', () => {
    expect(formatDate('not-a-date')).toBeNull();
  });

  it('formats a valid ISO date without the weekday', () => {
    // toDateString() → 'Sun Dec 14 2015'; the hook drops the leading weekday.
    expect(formatDate('2015-12-14')).toBe('Dec 14 2015');
  });
});

// Mount a hook inside a navigator + auth context so useFocusEffect and useAuth
// resolve exactly as they do in a real screen.
function renderHookInScreen(useHook: () => void, api: MockApi) {
  const Stack = createNativeStackNavigator();

  function Probe() {
    useHook();
    return <Text>probe</Text>;
  }

  return render(
    <AuthContext.Provider value={{ api: api as never, signOut: jest.fn() }}>
      <NavigationContainer>
        <Stack.Navigator>
          <Stack.Screen name="Probe" component={Probe} />
        </Stack.Navigator>
      </NavigationContainer>
    </AuthContext.Provider>,
  );
}

describe('useFocusedFetch', () => {
  it('exposes fetched data after focus', async () => {
    const api = mockApi();
    const fetcher = jest.fn().mockResolvedValue({ hello: 'world' });
    let captured: unknown;

    renderHookInScreen(() => {
      captured = useFocusedFetch(fetcher);
    }, api);

    await waitFor(() =>
      expect((captured as { data: unknown }).data).toEqual({ hello: 'world' }),
    );
    expect(fetcher).toHaveBeenCalled();
  });

  it('captures a fetch rejection as an error message', async () => {
    const api = mockApi();
    const fetcher = jest.fn().mockRejectedValue(new Error('backend down'));
    let captured: unknown;

    renderHookInScreen(() => {
      captured = useFocusedFetch(fetcher);
    }, api);

    await waitFor(() =>
      expect((captured as { error: string | null }).error).toBe('backend down'),
    );
  });
});

describe('useOptimisticDetail', () => {
  it('applies the optimistic edit immediately and issues the write', async () => {
    const api = mockApi();
    const show = makeShowDetail();
    api.getShow.mockResolvedValue(show);

    let hook: ReturnType<typeof useOptimisticDetail<typeof show>> | undefined;
    renderHookInScreen(() => {
      // Memoized like the real screens, so focus-refetch doesn't fire on every
      // render and stomp the optimistic edit.
      const fetcher = React.useCallback(() => api.getShow(show.id), []);
      hook = useOptimisticDetail('show', show.id, fetcher);
    }, api);

    await waitFor(() => expect(hook!.data).toBeTruthy());

    // Subscribe optimistically; the data should flip before the call settles.
    await act(async () => {
      hook!.setSubscription({ status: 'active' });
    });

    expect(api.subscribe).toHaveBeenCalledWith('show', show.id);
    await waitFor(() =>
      expect(hook!.data?.subscription).toEqual({ status: 'active' }),
    );
  });

  it('rolls back to server truth when the write fails', async () => {
    const api = mockApi();
    const show = makeShowDetail({ subscription: null });
    api.getShow.mockResolvedValue(show);
    api.subscribe.mockRejectedValueOnce(new Error('write failed'));

    let hook: ReturnType<typeof useOptimisticDetail<typeof show>> | undefined;
    renderHookInScreen(() => {
      const fetcher = React.useCallback(() => api.getShow(show.id), []);
      hook = useOptimisticDetail('show', show.id, fetcher);
    }, api);

    await waitFor(() => expect(hook!.data).toBeTruthy());

    await act(async () => {
      hook!.setSubscription({ status: 'active' });
    });

    // A failed write triggers a refetch; the refetched show has no subscription.
    await waitFor(() => expect(api.getShow).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(hook!.data?.subscription).toBeNull());
  });

  it('de-dupes a double-tap on the same target while one write is in flight', async () => {
    const api = mockApi();
    const show = makeShowDetail({ subscription: null });
    api.getShow.mockResolvedValue(show);

    // Hold the first subscribe open so the second tap lands mid-flight.
    let release: () => void = () => {};
    api.subscribe.mockReturnValue(
      new Promise<{ status: 'active' }>(resolve => {
        release = () => resolve({ status: 'active' });
      }),
    );

    let hook: ReturnType<typeof useOptimisticDetail<typeof show>> | undefined;
    renderHookInScreen(() => {
      const fetcher = React.useCallback(() => api.getShow(show.id), []);
      hook = useOptimisticDetail('show', show.id, fetcher);
    }, api);

    await waitFor(() => expect(hook!.data).toBeTruthy());

    await act(async () => {
      hook!.setSubscription({ status: 'active' });
      hook!.setSubscription({ status: 'active' });
    });

    expect(api.subscribe).toHaveBeenCalledTimes(1);

    await act(async () => {
      release();
    });
  });
});
