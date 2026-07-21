/* eslint-env jest */
import { fireEvent, screen, waitFor } from '@testing-library/react-native';
import ShowDetailScreen from '../../screens/ShowDetailScreen';
import { renderScreen } from '../helpers/renderWithProviders';
import { mockApi } from '../helpers/mockApi';
import { makeShowDetail } from '../helpers/fixtures';

describe('ShowDetailScreen', () => {
  it('shows a spinner until the show loads', () => {
    const api = mockApi();
    // Never resolves → stays in the loading state.
    api.getShow.mockReturnValue(new Promise(() => {}));

    renderScreen(ShowDetailScreen, { api, params: { showId: 1 } });

    expect(screen.UNSAFE_queryByType(require('react-native').ActivityIndicator)).not.toBeNull();
  });

  it('renders the show header and episodes on success', async () => {
    const api = mockApi();
    api.getShow.mockResolvedValue(makeShowDetail());

    renderScreen(ShowDetailScreen, { api, params: { showId: 1 } });

    await waitFor(() =>
      expect(screen.getByText('The Expanse')).toBeOnTheScreen(),
    );
    expect(screen.getByText(/Dulcinea/)).toBeOnTheScreen();
  });

  it('marks an episode watched optimistically and calls the API', async () => {
    const api = mockApi();
    api.getShow.mockResolvedValue(makeShowDetail());

    renderScreen(ShowDetailScreen, { api, params: { showId: 1 } });

    await waitFor(() =>
      expect(screen.getByText(/Dulcinea/)).toBeOnTheScreen(),
    );

    fireEvent.press(screen.getByText(/Dulcinea/));

    // Episode 100 starts unwatched → the toggle marks it watched (POST via true).
    await waitFor(() =>
      expect(api.setEpisodeWatched).toHaveBeenCalledWith(100, true),
    );
  });

  it('marks a whole season watched from the section header', async () => {
    const api = mockApi();
    api.getShow.mockResolvedValue(makeShowDetail());

    renderScreen(ShowDetailScreen, { api, params: { showId: 1 } });

    await waitFor(() =>
      expect(screen.getByText('Mark season watched')).toBeOnTheScreen(),
    );

    fireEvent.press(screen.getByText('Mark season watched'));

    await waitFor(() =>
      expect(api.setSeasonWatched).toHaveBeenCalledWith(10, true),
    );
  });

  it('renders the error text when the fetch fails', async () => {
    const api = mockApi();
    api.getShow.mockRejectedValue(new Error('show fetch failed'));

    renderScreen(ShowDetailScreen, { api, params: { showId: 1 } });

    await waitFor(() =>
      expect(screen.getByText('show fetch failed')).toBeOnTheScreen(),
    );
  });
});
