import React, { createContext, useCallback, useContext, useMemo } from 'react';
import { GoogleSignin } from '@react-native-google-signin/google-signin';
import { Api, AuthTokens } from './api';

interface AuthContextValue {
  api: Api;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/**
 * Holds the JWT pair in memory (persistence + refresh arrive with
 * Milestone 2.2) and exposes an authenticated Api client. A 401 from any
 * call signs the user out, dropping the app back to the Login screen.
 */
export function AuthProvider({
  tokens,
  onSignedOut,
  children,
}: {
  tokens: AuthTokens;
  onSignedOut: () => void;
  children: React.ReactNode;
}) {
  const signOut = useCallback(() => {
    GoogleSignin.signOut().catch(() => {});
    onSignedOut();
  }, [onSignedOut]);

  const api = useMemo(() => new Api(tokens.access, signOut), [tokens, signOut]);

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
