/* eslint-env jest */
import { screen, waitFor } from '@testing-library/react-native';
import HistoryScreen from '../../screens/HistoryScreen';
import { renderScreen } from '../helpers/renderWithProviders';
import { mockApi } from '../helpers/mockApi';
import { makeHistory } from '../helpers/fixtures';

describe('HistoryScreen', () => {
  it('renders episode and movie history rows', async () => {
    const api = mockApi();
    api.history.mockResolvedValue({ history: makeHistory() });

    renderScreen(HistoryScreen, { api });

    // Episode row composes the show title and the S1E1 code.
    await waitFor(() =>
      expect(screen.getByText(/The Expanse — S1E1/)).toBeOnTheScreen(),
    );
    expect(screen.getByText(/Dune/)).toBeOnTheScreen();
  });

  it('shows an empty state when nothing is watched', async () => {
    const api = mockApi();
    api.history.mockResolvedValue({ history: [] });

    renderScreen(HistoryScreen, { api });

    await waitFor(() =>
      expect(screen.getByText('Nothing watched yet')).toBeOnTheScreen(),
    );
  });

  it('renders the error text when the fetch fails', async () => {
    const api = mockApi();
    api.history.mockRejectedValue(new Error('history fetch failed'));

    renderScreen(HistoryScreen, { api });

    await waitFor(() =>
      expect(screen.getByText('history fetch failed')).toBeOnTheScreen(),
    );
  });
});
