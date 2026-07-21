import React, { createContext, useCallback, useContext, useMemo } from 'react';
import { GoogleSignin } from '@react-native-google-signin/google-signin';
import { Api, loginWithGoogle } from './api';
import {
  clearSession,
  saveSession,
  LoginProvider,
  StoredSession,
} from './sessionStore';

interface AuthContextValue {
  api: Api;
  signOut: () => void;
}

// Exported so tests can mount screens against a mock Api without standing up
// the real provider (which would require a live Google session and network).
export const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Re-establish an expired session without UI, using the provider the user
 * originally signed in with — never to pick a provider on their behalf.
 * Returns null when interactive sign-in is genuinely needed.
 */
export async function trySilentLogin(
  provider: LoginProvider,
): Promise<StoredSession | null> {
  if (provider !== 'google') {
    return null; // Facebook/Apple silent re-auth arrives with task 2.1
  }
  try {
    const response = await GoogleSignin.signInSilently();
    if (response.type !== 'success' || !response.data.idToken) {
      return null;
    }
    const session: StoredSession = {
      provider,
      tokens: await loginWithGoogle(response.data.idToken),
    };
    await saveSession(session);
    return session;
  } catch {
    return null;
  }
}

/**
 * Exposes an authenticated Api client for the stored session. Access tokens
 * refresh transparently (rotated pair persisted); when the refresh token
 * itself is rejected, `onAuthLost` fires with the session's provider so the
 * app can attempt a silent re-login before falling back to the Login screen.
 */
export function AuthProvider({
  session,
  onAuthLost,
  onSignedOut,
  children,
}: {
  session: StoredSession;
  onAuthLost: (provider: LoginProvider) => void;
  onSignedOut: () => void;
  children: React.ReactNode;
}) {
  const signOut = useCallback(() => {
    GoogleSignin.signOut().catch(() => {});
    clearSession();
    onSignedOut();
  }, [onSignedOut]);

  const api = useMemo(
    () =>
      new Api(
        session.tokens,
        tokens => saveSession({ provider: session.provider, tokens }),
        () => onAuthLost(session.provider),
      ),
    [session, onAuthLost],
  );

  const value = useMemo(() => ({ api, signOut }), [api, signOut]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return value;
}
