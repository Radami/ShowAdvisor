import React from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';
import { colors } from '../theme';

/**
 * Poster hotlinked from the provider CDN (spec §4.5 — the backend sends a
 * ready-to-load URL). Standard Image caching covers repeat views for now;
 * react-native-fast-image is the spec's named upgrade path if needed.
 */
export default function PosterImage({
  url,
  width = 56,
}: {
  url: string | null | undefined;
  width?: number;
}) {
  const size = { width, height: width * 1.5 };
  if (!url) {
    return (
      <View style={[styles.placeholder, size]}>
        <Text style={styles.placeholderText}>—</Text>
      </View>
    );
  }
  return <Image source={{ uri: url }} style={[styles.poster, size]} />;
}

const styles = StyleSheet.create({
  poster: {
    borderRadius: 6,
    backgroundColor: colors.surface,
  },
  placeholder: {
    borderRadius: 6,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderText: {
    color: colors.textMuted,
    fontSize: 18,
  },
});
