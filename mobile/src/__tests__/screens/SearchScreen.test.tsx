/* eslint-env jest */
import { fireEvent, screen, waitFor } from '@testing-library/react-native';
import SearchScreen from '../../screens/SearchScreen';
import { renderScreen } from '../helpers/renderWithProviders';
import { mockApi } from '../helpers/mockApi';
import { makeSearchResult } from '../helpers/fixtures';

const PLACEHOLDER = 'Search shows and movies…';

describe('SearchScreen', () => {
  it('runs a search on submit and renders the results', async () => {
    const api = mockApi();
    api.search.mockResolvedValue({
      query: 'expanse',
      results: [makeSearchResult({ title: 'The Expanse' })],
    });

    renderScreen(SearchScreen, { api });

    fireEvent.changeText(screen.getByPlaceholderText(PLACEHOLDER), 'expanse');
    fireEvent(screen.getByPlaceholderText(PLACEHOLDER), 'submitEditing');

    await waitFor(() =>
      expect(screen.getByText('The Expanse')).toBeOnTheScreen(),
    );
    expect(api.search).toHaveBeenCalledWith('expanse');
  });

  it('does not call the API for a blank query', async () => {
    const api = mockApi();

    renderScreen(SearchScreen, { api });

    fireEvent.changeText(screen.getByPlaceholderText(PLACEHOLDER), '   ');
    fireEvent(screen.getByPlaceholderText(PLACEHOLDER), 'submitEditing');

    expect(api.search).not.toHaveBeenCalled();
  });

  it('shows an empty state when nothing matches', async () => {
    const api = mockApi();
    api.search.mockResolvedValue({ query: 'zzz', results: [] });

    renderScreen(SearchScreen, { api });

    fireEvent.changeText(screen.getByPlaceholderText(PLACEHOLDER), 'zzz');
    fireEvent(screen.getByPlaceholderText(PLACEHOLDER), 'submitEditing');

    await waitFor(() =>
      expect(screen.getByText(/No matches for/)).toBeOnTheScreen(),
    );
  });

  it('renders the error message when the search fails, without crashing', async () => {
    const api = mockApi();
    api.search.mockRejectedValue(new Error('search backend down'));

    renderScreen(SearchScreen, { api });

    fireEvent.changeText(screen.getByPlaceholderText(PLACEHOLDER), 'expanse');
    fireEvent(screen.getByPlaceholderText(PLACEHOLDER), 'submitEditing');

    await waitFor(() =>
      expect(screen.getByText('search backend down')).toBeOnTheScreen(),
    );
  });
});
