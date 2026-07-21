/* eslint-env jest */
import { GoogleSignin } from '@react-native-google-signin/google-signin';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { trySilentLogin } from '../auth';
import * as api from '../api';
import { loadSession } from '../sessionStore';
import { makeTokens } from './helpers/fixtures';

jest.mock('@react-native-google-signin/google-signin', () => ({
  GoogleSignin: {
    signInSilently: jest.fn(),
    signOut: jest.fn(),
  },
}));

const signInSilently = GoogleSignin.signInSilently as jest.Mock;

afterEach(async () => {
  await AsyncStorage.clear();
  jest.restoreAllMocks();
  jest.clearAllMocks();
});

describe('trySilentLogin', () => {
  it('returns null for a provider that has no silent path yet', async () => {
    // Facebook/Apple silent re-auth arrives with task 2.1.
    await expect(trySilentLogin('facebook' as never)).resolves.toBeNull();
    expect(signInSilently).not.toHaveBeenCalled();
  });

  it('exchanges the silent ID token and persists the session on success', async () => {
    signInSilently.mockResolvedValue({
      type: 'success',
      data: { idToken: 'silent-id-token' },
    });
    const tokens = makeTokens();
    jest.spyOn(api, 'loginWithGoogle').mockResolvedValue(tokens);

    const session = await trySilentLogin('google');

    expect(session).toEqual({ provider: 'google', tokens });
    // The recovered session is written through so the next launch restores it.
    await expect(loadSession()).resolves.toEqual({ provider: 'google', tokens });
  });

  it('returns null when Google reports no silent session', async () => {
    signInSilently.mockResolvedValue({ type: 'noSavedCredentialFound' });

    await expect(trySilentLogin('google')).resolves.toBeNull();
  });

  it('returns null when the silent response carries no ID token', async () => {
    signInSilently.mockResolvedValue({ type: 'success', data: { idToken: null } });

    await expect(trySilentLogin('google')).resolves.toBeNull();
  });

  it('returns null (not a throw) when the token exchange fails', async () => {
    signInSilently.mockResolvedValue({
      type: 'success',
      data: { idToken: 'silent-id-token' },
    });
    jest.spyOn(api, 'loginWithGoogle').mockRejectedValue(new Error('backend 500'));

    await expect(trySilentLogin('google')).resolves.toBeNull();
  });

  it('returns null (not a throw) when the silent sign-in itself throws', async () => {
    signInSilently.mockRejectedValue(new Error('play services missing'));

    await expect(trySilentLogin('google')).resolves.toBeNull();
  });
});
