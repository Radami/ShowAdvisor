/* eslint-env jest */
import { fireEvent, screen, waitFor } from '@testing-library/react-native';
import MovieDetailScreen from '../../screens/MovieDetailScreen';
import { renderScreen } from '../helpers/renderWithProviders';
import { mockApi } from '../helpers/mockApi';
import { makeMovieDetail } from '../helpers/fixtures';

describe('MovieDetailScreen', () => {
  it('renders the movie header on success', async () => {
    const api = mockApi();
    api.getMovie.mockResolvedValue(makeMovieDetail());

    renderScreen(MovieDetailScreen, { api, params: { movieId: 5 } });

    await waitFor(() => expect(screen.getByText('Dune')).toBeOnTheScreen());
    expect(screen.getByText('Mark as watched')).toBeOnTheScreen();
  });

  it('toggles watched optimistically and calls the API', async () => {
    const api = mockApi();
    api.getMovie.mockResolvedValue(makeMovieDetail({ watched: false }));

    renderScreen(MovieDetailScreen, { api, params: { movieId: 5 } });

    await waitFor(() =>
      expect(screen.getByText('Mark as watched')).toBeOnTheScreen(),
    );

    fireEvent.press(screen.getByText('Mark as watched'));

    await waitFor(() =>
      expect(api.setMovieWatched).toHaveBeenCalledWith(5, true),
    );
    // Optimistic flip: the label switches before any refetch.
    await waitFor(() => expect(screen.getByText('✓ Watched')).toBeOnTheScreen());
  });

  it('subscribes via the subscribe action', async () => {
    const api = mockApi();
    api.getMovie.mockResolvedValue(makeMovieDetail({ subscription: null }));

    renderScreen(MovieDetailScreen, { api, params: { movieId: 5 } });

    await waitFor(() => expect(screen.getByText('Subscribe')).toBeOnTheScreen());

    fireEvent.press(screen.getByText('Subscribe'));

    await waitFor(() => expect(api.subscribe).toHaveBeenCalledWith('movie', 5));
  });

  it('renders the error text when the fetch fails', async () => {
    const api = mockApi();
    api.getMovie.mockRejectedValue(new Error('movie fetch failed'));

    renderScreen(MovieDetailScreen, { api, params: { movieId: 5 } });

    await waitFor(() =>
      expect(screen.getByText('movie fetch failed')).toBeOnTheScreen(),
    );
  });
});
