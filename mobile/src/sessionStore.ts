import AsyncStorage from '@react-native-async-storage/async-storage';
import { AuthTokens } from './api';

/** Sign-in methods the app supports; 'facebook' and 'apple' arrive with task 2.1. */
export type LoginProvider = 'google';

/**
 * What survives between launches: the JWT pair plus the provider the user
 * chose on the Login screen. The provider is remembered so an expired
 * session can be re-established silently with the same method — it is never
 * guessed: a fresh install (or signed-out state) always prompts.
 */
export interface StoredSession {
  provider: LoginProvider;
  tokens: AuthTokens;
}

const KEY = 'showadvisor.session';

/** Storage failures are swallowed — worst case is an explicit sign-in. */
export async function loadSession(): Promise<StoredSession | null> {
  try {
    const raw = await AsyncStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as StoredSession) : null;
  } catch {
    return null;
  }
}

export async function saveSession(session: StoredSession): Promise<void> {
  try {
    await AsyncStorage.setItem(KEY, JSON.stringify(session));
  } catch {
    // ignore — next launch just re-authenticates
  }
}

export async function clearSession(): Promise<void> {
  try {
    await AsyncStorage.removeItem(KEY);
  } catch {
    // ignore
  }
}
