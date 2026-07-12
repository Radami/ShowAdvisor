/**
 * ShowAdvisor — Milestone 6: real navigation shell.
 * Login (Google Sign-In, Milestone 0 flow) -> bottom tabs
 * (Search / Shows / Movies / Profile, spec §3.1) with detail screens and
 * Watch History pushed on a native stack above the tabs.
 *
 * @format
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import type { ComponentProps } from 'react';
import { ActivityIndicator, StatusBar, StyleSheet } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import Ionicons from '@react-native-vector-icons/ionicons';
import { GoogleSignin } from '@react-native-google-signin/google-signin';
import { AuthProvider, trySilentLogin } from './src/auth';
import {
  loadSession,
  saveSession,
  LoginProvider,
  StoredSession,
} from './src/sessionStore';
import { GOOGLE_WEB_CLIENT_ID } from './src/config';
import { RootStackParamList, TabParamList } from './src/navigation';
import { colors } from './src/theme';
import LoginScreen from './src/screens/LoginScreen';
import SearchScreen from './src/screens/SearchScreen';
import ShowsScreen from './src/screens/ShowsScreen';
import MoviesScreen from './src/screens/MoviesScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import ShowDetailScreen from './src/screens/ShowDetailScreen';
import MovieDetailScreen from './src/screens/MovieDetailScreen';
import HistoryScreen from './src/screens/HistoryScreen';

const Tab = createBottomTabNavigator<TabParamList>();
const Stack = createNativeStackNavigator<RootStackParamList>();

type IconName = ComponentProps<typeof Ionicons>['name'];

// Ionicons: filled glyph on the active tab, outline variant otherwise.
const TAB_ICONS: Record<keyof TabParamList, { active: IconName; inactive: IconName }> = {
  Search: { active: 'search', inactive: 'search-outline' },
  Shows: { active: 'tv', inactive: 'tv-outline' },
  Movies: { active: 'film', inactive: 'film-outline' },
  Profile: { active: 'person', inactive: 'person-outline' },
};

// Module scope so React sees stable component types across renders.
const tabScreenOptions = ({ route }: { route: { name: keyof TabParamList } }) => ({
  tabBarIcon: ({ focused, color, size }: { focused: boolean; color: string; size: number }) => (
    <Ionicons
      name={TAB_ICONS[route.name][focused ? 'active' : 'inactive']}
      size={size}
      color={color}
    />
  ),
  tabBarActiveTintColor: colors.accent,
  tabBarInactiveTintColor: colors.textMuted,
});

function Tabs() {
  return (
    // Shows opens first (§3.1): the everyday screen is your watch list,
    // while Search keeps the leftmost slot in the bar.
    <Tab.Navigator initialRouteName="Shows" screenOptions={tabScreenOptions}>
      <Tab.Screen name="Search" component={SearchScreen} />
      <Tab.Screen name="Shows" component={ShowsScreen} />
      <Tab.Screen name="Movies" component={MoviesScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

function App() {
  const [session, setSession] = useState<StoredSession | null>(null);
  // True while the stored session is being restored at launch. A fresh
  // install (or signed-out state) has nothing stored and always prompts for
  // a sign-in method — the provider choice is the user's, never inferred
  // from device state (Milestone 2.2; Facebook/Apple arrive with 2.1).
  const [restoring, setRestoring] = useState(true);
  const recovering = useRef(false);

  useEffect(() => {
    GoogleSignin.configure({ webClientId: GOOGLE_WEB_CLIENT_ID });
    (async () => {
      setSession(await loadSession());
      setRestoring(false);
    })();
  }, []);

  const handleLoggedIn = useCallback((fresh: StoredSession) => {
    saveSession(fresh);
    setSession(fresh);
  }, []);

  // Refresh token rejected mid-session: re-authenticate silently with the
  // same provider the user signed in with; only if that also fails does the
  // app drop back to the Login screen.
  const handleAuthLost = useCallback(async (provider: LoginProvider) => {
    if (recovering.current) {
      return; // several requests can 401 together — recover once
    }
    recovering.current = true;
    try {
      setSession(await trySilentLogin(provider));
    } finally {
      recovering.current = false;
    }
  }, []);

  if (restoring) {
    return (
      <SafeAreaProvider>
        <StatusBar barStyle="dark-content" />
        <SafeAreaView style={styles.loginContainer}>
          <ActivityIndicator style={styles.restoreSpinner} size="large" />
        </SafeAreaView>
      </SafeAreaProvider>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar barStyle="dark-content" />
      {session ? (
        <AuthProvider
          session={session}
          onAuthLost={handleAuthLost}
          onSignedOut={() => setSession(null)}
        >
          <NavigationContainer>
            <Stack.Navigator>
              <Stack.Screen name="Tabs" component={Tabs} options={{ headerShown: false }} />
              <Stack.Screen
                name="ShowDetail"
                component={ShowDetailScreen}
                options={({ route }) => ({ title: route.params.title ?? 'Show' })}
              />
              <Stack.Screen
                name="MovieDetail"
                component={MovieDetailScreen}
                options={({ route }) => ({ title: route.params.title ?? 'Movie' })}
              />
              <Stack.Screen
                name="History"
                component={HistoryScreen}
                options={{ title: 'Watch History' }}
              />
            </Stack.Navigator>
          </NavigationContainer>
        </AuthProvider>
      ) : (
        <SafeAreaView style={styles.loginContainer}>
          <LoginScreen onLoggedIn={handleLoggedIn} />
        </SafeAreaView>
      )}
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  loginContainer: {
    flex: 1,
  },
  restoreSpinner: {
    flex: 1,
  },
});

export default App;
