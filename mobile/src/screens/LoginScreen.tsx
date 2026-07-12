import React, { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {
  GoogleSignin,
  isSuccessResponse,
} from '@react-native-google-signin/google-signin';
import { loginWithGoogle } from '../api';
import { StoredSession } from '../sessionStore';

interface Props {
  onLoggedIn: (session: StoredSession) => void;
}

export default function LoginScreen({ onLoggedIn }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const signIn = async () => {
    setBusy(true);
    setError(null);
    try {
      await GoogleSignin.hasPlayServices();
      const response = await GoogleSignin.signIn();
      if (!isSuccessResponse(response)) {
        return; // user cancelled
      }
      const idToken = response.data.idToken;
      if (!idToken) {
        throw new Error('Google returned no ID token — check webClientId config');
      }
      // The chosen provider is stored with the session — this screen is the
      // one place the sign-in method gets decided (more providers: task 2.1).
      onLoggedIn({ provider: 'google', tokens: await loginWithGoogle(idToken) });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>ShowAdvisor</Text>
      {busy ? (
        <ActivityIndicator size="large" />
      ) : (
        <Pressable style={styles.button} onPress={signIn}>
          <Text style={styles.buttonText}>Sign in with Google</Text>
        </Pressable>
      )}
      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 24,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
  },
  button: {
    backgroundColor: '#4285F4',
    paddingVertical: 12,
    paddingHorizontal: 32,
    borderRadius: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  error: {
    color: '#c0392b',
    textAlign: 'center',
  },
});
