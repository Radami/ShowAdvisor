import React, { useCallback, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../auth';
import { MovieListItem } from '../api';
import { RootNavigation } from '../navigation';
import { colors } from '../theme';
import { formatDate, useFocusedFetch } from '../hooks';
import EmptyState from '../components/EmptyState';
import SegmentedTabs from '../components/SegmentedTabs';
import TitleRow from '../components/TitleRow';

type BucketKey = 'watch_list' | 'up_next' | 'paused';

const TABS: { key: BucketKey; label: string }[] = [
  { key: 'watch_list', label: 'Watch list' },
  { key: 'up_next', label: 'Up next' },
  { key: 'paused', label: 'Paused' },
];

const EMPTY_HINTS: Record<BucketKey, string> = {
  watch_list: 'Movies you subscribe to stay here until you’ve watched them.',
  up_next: 'Movies you track that aren’t released yet appear here.',
  paused: 'Movies you pause ("watch later") appear here.',
};

function subtitle(item: MovieListItem): string {
  const date = formatDate(item.release_date);
  if (!date) {
    return 'Release date TBA';
  }
  const released = new Date(item.release_date as string) <= new Date();
  return released ? `Released ${date}` : `Releases ${date}`;
}

/** Movies tab (spec §3.1) — same three-bucket pattern as Shows. */
export default function MoviesScreen() {
  const { api } = useAuth();
  const navigation = useNavigation<RootNavigation>();
  const [bucket, setBucket] = useState<BucketKey>('watch_list');
  const { data, error, reload } = useFocusedFetch(useCallback(() => api.myMovies(), [api]));

  const togglePause = async (item: MovieListItem) => {
    await api.setSubscriptionStatus(
      'movie',
      item.id,
      item.subscription_status === 'paused' ? 'active' : 'paused',
    );
    reload();
  };

  if (error) {
    return <Text style={styles.error}>{error}</Text>;
  }
  if (!data) {
    return <ActivityIndicator style={styles.spinner} size="large" />;
  }

  const items = data[bucket];
  return (
    <View style={styles.container}>
      <SegmentedTabs tabs={TABS} selected={bucket} onSelect={setBucket} />
      <FlatList
        data={items}
        keyExtractor={item => String(item.id)}
        renderItem={({ item }) => (
          <TitleRow
            title={item.title}
            subtitle={subtitle(item)}
            posterUrl={item.poster_url}
            onPress={() =>
              navigation.navigate('MovieDetail', { movieId: item.id, title: item.title })
            }
            actionLabel={bucket === 'paused' ? 'Resume' : 'Pause'}
            onAction={() => togglePause(item)}
          />
        )}
        ListEmptyComponent={
          <EmptyState
            message="No movies tracked yet"
            hint={`${EMPTY_HINTS[bucket]} Find movies in Search and subscribe.`}
          />
        }
        contentContainerStyle={items.length === 0 ? styles.emptyFill : undefined}
      />
    </View>
  );
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
  emptyFill: {
    flexGrow: 1,
  },
});
