/* eslint-env jest */
import { screen, waitFor } from '@testing-library/react-native';
import MoviesScreen from '../../screens/MoviesScreen';
import { renderScreen } from '../helpers/renderWithProviders';
import { mockApi } from '../helpers/mockApi';
import { makeMovieBuckets } from '../helpers/fixtures';

describe('MoviesScreen (BucketListScreen)', () => {
  it('renders tracked movies with a release subtitle', async () => {
    const api = mockApi();
    api.myMovies.mockResolvedValue(makeMovieBuckets());

    renderScreen(MoviesScreen, { api });

    await waitFor(() => expect(screen.getByText('Dune')).toBeOnTheScreen());
    // A past release_date renders as "Released …".
    expect(screen.getByText(/Released/)).toBeOnTheScreen();
  });

  it('shows an empty state for an empty bucket', async () => {
    const api = mockApi();
    api.myMovies.mockResolvedValue({ watch_list: [], up_next: [], paused: [] });

    renderScreen(MoviesScreen, { api });

    await waitFor(() =>
      expect(screen.getByText('No movies tracked yet')).toBeOnTheScreen(),
    );
  });

  it('renders the error text when the fetch fails', async () => {
    const api = mockApi();
    api.myMovies.mockRejectedValue(new Error('movies fetch failed'));

    renderScreen(MoviesScreen, { api });

    await waitFor(() =>
      expect(screen.getByText('movies fetch failed')).toBeOnTheScreen(),
    );
  });
});
