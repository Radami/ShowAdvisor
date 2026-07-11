/**
 * ShowAdvisor — Milestone 0 walking skeleton.
 * Two screens, no tab navigation yet (that comes in Milestone 6):
 * Login (Google Sign-In) -> Profile (real data from the Dockerized backend).
 *
 * @format
 */

import React, { useEffect, useState } from 'react';
import { StatusBar, StyleSheet, useColorScheme, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { GoogleSignin } from '@react-native-google-signin/google-signin';
import { AuthTokens } from './src/api';
import { GOOGLE_WEB_CLIENT_ID } from './src/config';
import LoginScreen from './src/screens/LoginScreen';
import ProfileScreen from './src/screens/ProfileScreen';

function App() {
  const isDarkMode = useColorScheme() === 'dark';
  const [tokens, setTokens] = useState<AuthTokens | null>(null);

  useEffect(() => {
    GoogleSignin.configure({ webClientId: GOOGLE_WEB_CLIENT_ID });
  }, []);

  return (
    <SafeAreaProvider>
      <StatusBar barStyle={isDarkMode ? 'light-content' : 'dark-content'} />
      <SafeAreaView style={styles.container}>
        {tokens ? (
          <ProfileScreen accessToken={tokens.access} />
        ) : (
          <LoginScreen onLoggedIn={setTokens} />
        )}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});

export default App;
