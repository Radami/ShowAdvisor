/* eslint-env jest */
import { fireEvent, screen, waitFor } from '@testing-library/react-native';
import ProfileScreen from '../../screens/ProfileScreen';
import { renderScreen } from '../helpers/renderWithProviders';
import { mockApi } from '../helpers/mockApi';
import { makeProfile } from '../helpers/fixtures';

describe('ProfileScreen', () => {
  it('renders the username and email', async () => {
    const api = mockApi();
    api.getProfile.mockResolvedValue(makeProfile());

    renderScreen(ProfileScreen, { api });

    await waitFor(() => expect(screen.getByText('ada')).toBeOnTheScreen());
    expect(screen.getByText('ada@example.com')).toBeOnTheScreen();
  });

  it('signs out when the sign-out row is pressed', async () => {
    const api = mockApi();
    api.getProfile.mockResolvedValue(makeProfile());
    const signOut = jest.fn();

    renderScreen(ProfileScreen, { api, signOut });

    await waitFor(() => expect(screen.getByText('Sign out')).toBeOnTheScreen());

    fireEvent.press(screen.getByText('Sign out'));
    expect(signOut).toHaveBeenCalledTimes(1);
  });

  it('renders the error text when the profile fetch fails', async () => {
    const api = mockApi();
    api.getProfile.mockRejectedValue(new Error('profile fetch failed'));

    renderScreen(ProfileScreen, { api });

    await waitFor(() =>
      expect(screen.getByText('profile fetch failed')).toBeOnTheScreen(),
    );
  });
});
