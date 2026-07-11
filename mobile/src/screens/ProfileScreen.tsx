import React, { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { fetchProfile, Profile } from '../api';

interface Props {
  accessToken: string;
}

export default function ProfileScreen({ accessToken }: Props) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProfile(accessToken)
      .then(setProfile)
      .catch(e => setError(e instanceof Error ? e.message : String(e)));
  }, [accessToken]);

  if (error) {
    return (
      <View style={styles.container}>
        <Text style={styles.error}>{error}</Text>
      </View>
    );
  }

  if (!profile) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.heading}>Profile</Text>
      <View style={styles.row}>
        <Text style={styles.label}>Username</Text>
        <Text style={styles.value}>{profile.username}</Text>
      </View>
      <View style={styles.row}>
        <Text style={styles.label}>Email</Text>
        <Text style={styles.value}>{profile.email}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    gap: 16,
  },
  heading: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  row: {
    alignItems: 'center',
    gap: 4,
  },
  label: {
    fontSize: 13,
    textTransform: 'uppercase',
    opacity: 0.6,
  },
  value: {
    fontSize: 18,
  },
  error: {
    color: '#c0392b',
    textAlign: 'center',
  },
});
