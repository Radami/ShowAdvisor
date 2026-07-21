/* eslint-env jest */
import React from 'react';
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react-native';
import {
  GoogleSignin,
  isSuccessResponse,
} from '@react-native-google-signin/google-signin';
import LoginScreen from '../../screens/LoginScreen';
import * as api from '../../api';
import { makeTokens } from '../helpers/fixtures';

jest.mock('@react-native-google-signin/google-signin', () => ({
  GoogleSignin: {
    hasPlayServices: jest.fn().mockResolvedValue(true),
    signIn: jest.fn(),
  },
  isSuccessResponse: jest.fn(),
}));

const signIn = GoogleSignin.signIn as jest.Mock;
const asSuccess = isSuccessResponse as unknown as jest.Mock;

afterEach(() => {
  jest.clearAllMocks();
  jest.restoreAllMocks();
});

describe('LoginScreen', () => {
  it('signs in and reports the session on success', async () => {
    signIn.mockResolvedValue({ data: { idToken: 'google-id-token' } });
    asSuccess.mockReturnValue(true);
    const tokens = makeTokens();
    jest.spyOn(api, 'loginWithGoogle').mockResolvedValue(tokens);
    const onLoggedIn = jest.fn();

    render(<LoginScreen onLoggedIn={onLoggedIn} />);
    fireEvent.press(screen.getByText('Sign in with Google'));

    await waitFor(() =>
      expect(onLoggedIn).toHaveBeenCalledWith({ provider: 'google', tokens }),
    );
  });

  it('does nothing when the user cancels the Google prompt', async () => {
    signIn.mockResolvedValue({ type: 'cancelled' });
    asSuccess.mockReturnValue(false); // not a success response
    const loginSpy = jest.spyOn(api, 'loginWithGoogle');
    const onLoggedIn = jest.fn();

    render(<LoginScreen onLoggedIn={onLoggedIn} />);
    fireEvent.press(screen.getByText('Sign in with Google'));

    await waitFor(() => expect(signIn).toHaveBeenCalled());
    // Cancelling is not an error: no token exchange, no callback, no message.
    expect(loginSpy).not.toHaveBeenCalled();
    expect(onLoggedIn).not.toHaveBeenCalled();
    expect(screen.queryByText(/token/i)).toBeNull();
  });

  it('shows an error when Google returns no ID token', async () => {
    signIn.mockResolvedValue({ data: { idToken: null } });
    asSuccess.mockReturnValue(true);
    const onLoggedIn = jest.fn();

    render(<LoginScreen onLoggedIn={onLoggedIn} />);
    fireEvent.press(screen.getByText('Sign in with Google'));

    await waitFor(() =>
      expect(screen.getByText(/no ID token/i)).toBeOnTheScreen(),
    );
    expect(onLoggedIn).not.toHaveBeenCalled();
  });

  it('surfaces a thrown sign-in error and clears the busy state', async () => {
    signIn.mockRejectedValue(new Error('play services unavailable'));
    const onLoggedIn = jest.fn();

    render(<LoginScreen onLoggedIn={onLoggedIn} />);
    fireEvent.press(screen.getByText('Sign in with Google'));

    await waitFor(() =>
      expect(screen.getByText('play services unavailable')).toBeOnTheScreen(),
    );
    // Busy cleared → the button is back so the user can retry.
    expect(screen.getByText('Sign in with Google')).toBeOnTheScreen();
    expect(onLoggedIn).not.toHaveBeenCalled();
  });
});
