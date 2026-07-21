/* eslint-env jest */
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  clearSession,
  loadSession,
  saveSession,
  StoredSession,
} from '../sessionStore';
import { makeTokens } from './helpers/fixtures';

const SESSION: StoredSession = { provider: 'google', tokens: makeTokens() };

afterEach(async () => {
  await AsyncStorage.clear();
  jest.restoreAllMocks();
});

describe('sessionStore — happy path', () => {
  it('round-trips a saved session', async () => {
    await saveSession(SESSION);

    await expect(loadSession()).resolves.toEqual(SESSION);
  });

  it('returns null when nothing is stored', async () => {
    await expect(loadSession()).resolves.toBeNull();
  });

  it('removes the session on clear', async () => {
    await saveSession(SESSION);

    await clearSession();

    await expect(loadSession()).resolves.toBeNull();
  });
});

describe('sessionStore — graceful failure', () => {
  it('returns null (not a throw) for a corrupt stored value', async () => {
    // Write raw garbage past the typed API to simulate a partial/older write.
    await AsyncStorage.setItem('showadvisor.session', '{ not json');

    await expect(loadSession()).resolves.toBeNull();
  });

  it('swallows a read failure and returns null', async () => {
    jest
      .spyOn(AsyncStorage, 'getItem')
      .mockRejectedValueOnce(new Error('storage unavailable'));

    await expect(loadSession()).resolves.toBeNull();
  });

  it('swallows a write failure without throwing', async () => {
    jest
      .spyOn(AsyncStorage, 'setItem')
      .mockRejectedValueOnce(new Error('disk full'));

    await expect(saveSession(SESSION)).resolves.toBeUndefined();
  });

  it('swallows a clear failure without throwing', async () => {
    jest
      .spyOn(AsyncStorage, 'removeItem')
      .mockRejectedValueOnce(new Error('storage unavailable'));

    await expect(clearSession()).resolves.toBeUndefined();
  });
});
