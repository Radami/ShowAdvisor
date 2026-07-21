/* eslint-env jest */
import { Alert } from 'react-native';
import { fireEvent, screen, waitFor } from '@testing-library/react-native';
import ShowsScreen from '../../screens/ShowsScreen';
import { renderScreen } from '../helpers/renderWithProviders';
import { mockApi } from '../helpers/mockApi';
import { makeShowBuckets } from '../helpers/fixtures';

describe('ShowsScreen (BucketListScreen)', () => {
  it('renders the default Watch list bucket', async () => {
    const api = mockApi();
    api.myShows.mockResolvedValue(makeShowBuckets());

    renderScreen(ShowsScreen, { api });

    await waitFor(() =>
      expect(screen.getByText('The Expanse')).toBeOnTheScreen(),
    );
    // Watch list subtitle reflects the unwatched count.
    expect(screen.getByText('3 episodes to watch')).toBeOnTheScreen();
  });

  it('switches to another bucket when its tab is pressed', async () => {
    const api = mockApi();
    api.myShows.mockResolvedValue(makeShowBuckets());

    renderScreen(ShowsScreen, { api });

    await waitFor(() =>
      expect(screen.getByText('The Expanse')).toBeOnTheScreen(),
    );

    fireEvent.press(screen.getByText('Up next'));

    // Up next holds a different show than the watch list.
    await waitFor(() => expect(screen.getByText('Severance')).toBeOnTheScreen());
  });

  it('shows an empty state for an empty bucket', async () => {
    const api = mockApi();
    api.myShows.mockResolvedValue({ watch_list: [], up_next: [], paused: [] });

    renderScreen(ShowsScreen, { api });

    await waitFor(() =>
      expect(screen.getByText('No shows tracked yet')).toBeOnTheScreen(),
    );
  });

  it('renders the error text when the fetch fails', async () => {
    const api = mockApi();
    api.myShows.mockRejectedValue(new Error('shows fetch failed'));

    renderScreen(ShowsScreen, { api });

    await waitFor(() =>
      expect(screen.getByText('shows fetch failed')).toBeOnTheScreen(),
    );
  });

  it('alerts and reloads when a pause toggle fails', async () => {
    const api = mockApi();
    api.myShows.mockResolvedValue(makeShowBuckets());
    api.setSubscriptionStatus.mockRejectedValue(new Error('pause failed'));
    const alertSpy = jest.spyOn(Alert, 'alert').mockImplementation(() => {});

    renderScreen(ShowsScreen, { api });

    await waitFor(() =>
      expect(screen.getByText('The Expanse')).toBeOnTheScreen(),
    );

    // The Watch list row's inline action pauses an active subscription.
    fireEvent.press(screen.getAllByText('Pause')[0]);

    await waitFor(() =>
      expect(alertSpy).toHaveBeenCalledWith('Could not update', 'pause failed'),
    );
    // Reloaded once on mount, once after the failed toggle → server truth.
    expect(api.myShows.mock.calls.length).toBeGreaterThanOrEqual(2);
  });
});
