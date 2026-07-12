/**
 * ShowAdvisor — Milestone 6: real navigation shell.
 * Login (Google Sign-In, Milestone 0 flow) -> bottom tabs
 * (Search / Shows / Movies / Profile, spec §3.1) with detail screens and
 * Watch History pushed on a native stack above the tabs.
 *
 * @format
 */

import React, { useEffect, useState } from 'react';
import type { ComponentProps } from 'react';
import { StatusBar, StyleSheet } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import Ionicons from '@react-native-vector-icons/ionicons';
import { GoogleSignin } from '@react-native-google-signin/google-signin';
import { AuthTokens } from './src/api';
import { AuthProvider } from './src/auth';
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
    <Tab.Navigator screenOptions={tabScreenOptions}>
      <Tab.Screen name="Search" component={SearchScreen} />
      <Tab.Screen name="Shows" component={ShowsScreen} />
      <Tab.Screen name="Movies" component={MoviesScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

function App() {
  const [tokens, setTokens] = useState<AuthTokens | null>(null);

  useEffect(() => {
    GoogleSignin.configure({ webClientId: GOOGLE_WEB_CLIENT_ID });
  }, []);

  return (
    <SafeAreaProvider>
      <StatusBar barStyle="dark-content" />
      {tokens ? (
        <AuthProvider tokens={tokens} onSignedOut={() => setTokens(null)}>
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
          <LoginScreen onLoggedIn={setTokens} />
        </SafeAreaView>
      )}
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  loginContainer: {
    flex: 1,
  },
});

export default App;
