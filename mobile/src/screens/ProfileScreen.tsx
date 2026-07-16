import React, { useCallback } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../auth';
import { RootNavigation } from '../navigation';
import { colors } from '../theme';
import { useFocusedFetch } from '../hooks';

/**
 * Profile tab — username/email, Watch History link, sign out. The full
 * Profile content (subscription status, TMDB attribution, Privacy
 * Policy/ToS, delete account, contact support) is assembled in Milestone 9.
 */
export default function ProfileScreen() {
  const { api, signOut } = useAuth();
  const navigation = useNavigation<RootNavigation>();
  const { data: profile, error } = useFocusedFetch(
    useCallback(() => api.getProfile(), [api]),
  );

  if (error) {
    return <Text style={styles.error}>{error}</Text>;
  }
  if (!profile) {
    return <ActivityIndicator style={styles.spinner} size="large" />;
  }

  return (
    <View style={styles.container}>
      <View style={styles.identity}>
        <Text style={styles.username}>{profile.username}</Text>
        <Text style={styles.email}>{profile.email}</Text>
      </View>

      <Pressable style={styles.linkRow} onPress={() => navigation.navigate('History')}>
        <Text style={styles.linkText}>Watch History</Text>
        <Text style={styles.chevron}>›</Text>
      </Pressable>

      <Pressable style={styles.linkRow} onPress={signOut}>
        <Text style={[styles.linkText, styles.signOut]}>Sign out</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    paddingTop: 24,
  },
  spinner: {
    marginTop: 32,
  },
  error: {
    color: colors.danger,
    textAlign: 'center',
    margin: 24,
  },
  identity: {
    alignItems: 'center',
    gap: 4,
    paddingBottom: 24,
  },
  username: {
    fontSize: 22,
    fontWeight: 'bold',
    color: colors.text,
  },
  email: {
    fontSize: 14,
    color: colors.textMuted,
  },
  linkRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  linkText: {
    fontSize: 16,
    color: colors.text,
  },
  chevron: {
    fontSize: 20,
    color: colors.textMuted,
  },
  signOut: {
    color: colors.danger,
  },
});
