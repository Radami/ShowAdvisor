import React, { useCallback } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../auth';
import { HistoryItem } from '../api';
import { RootNavigation } from '../navigation';
import { colors } from '../theme';
import { formatDate, useFocusedFetch } from '../hooks';
import EmptyState from '../components/EmptyState';

function itemTitle(item: HistoryItem): string {
  if (item.type === 'movie') {
    return item.title;
  }
  const episodeNumber =
    item.episode_number != null
      ? `S${item.season_number}E${item.episode_number}`
      : `S${item.season_number} Special`;
  return `${item.show_title} — ${episodeNumber}`;
}

/**
 * Watch History screen (spec §3.1): everything marked watched, most recent
 * first — the one place watched items remain visible after leaving the
 * Watching/Up next lists.
 */
export default function HistoryScreen() {
  const { api } = useAuth();
  const navigation = useNavigation<RootNavigation>();
  const { data, error } = useFocusedFetch(useCallback(() => api.history(), [api]));

  if (error) {
    return <Text style={styles.error}>{error}</Text>;
  }
  if (!data) {
    return <ActivityIndicator style={styles.spinner} size="large" />;
  }

  const openItem = (item: HistoryItem) => {
    if (item.type === 'episode' && item.show_id) {
      navigation.navigate('ShowDetail', { showId: item.show_id, title: item.show_title });
    } else if (item.type === 'movie' && item.movie_id) {
      navigation.navigate('MovieDetail', { movieId: item.movie_id, title: item.title });
    }
  };

  return (
    <FlatList
      style={styles.container}
      data={data.history}
      keyExtractor={(item, index) => `${item.type}-${index}`}
      renderItem={({ item }) => (
        <Text style={styles.row} onPress={() => openItem(item)}>
          <Text style={styles.rowTitle}>{itemTitle(item)}</Text>
          {item.type === 'episode' && item.title ? (
            <Text style={styles.rowSubtitle}> · {item.title}</Text>
          ) : null}
          <Text style={styles.rowSubtitle}>
            {'\n'}
            {formatDate(item.watched_at)}
          </Text>
        </Text>
      )}
      ItemSeparatorComponent={Separator}
      ListEmptyComponent={
        <EmptyState
          message="Nothing watched yet"
          hint="Episodes and movies you mark watched appear here."
        />
      }
      contentContainerStyle={data.history.length === 0 ? styles.emptyFill : undefined}
    />
  );
}

function Separator() {
  return <View style={styles.separator} />;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  spinner: {
    marginTop: 32,
  },
  error: {
    color: colors.danger,
    textAlign: 'center',
    margin: 24,
  },
  row: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    lineHeight: 20,
  },
  rowTitle: {
    fontWeight: '600',
    color: colors.text,
  },
  rowSubtitle: {
    color: colors.textMuted,
    fontSize: 13,
  },
  separator: {
    height: StyleSheet.hairlineWidth,
    backgroundColor: colors.border,
    marginLeft: 16,
  },
  emptyFill: {
    flexGrow: 1,
  },
});
