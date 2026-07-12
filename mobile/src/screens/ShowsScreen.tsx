import React, { useCallback, useState } from 'react';
import { ActivityIndicator, FlatList, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../auth';
import { ShowListItem } from '../api';
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
  watch_list: 'Shows you subscribe to stay here until you’ve watched every episode.',
  up_next: 'Shows with upcoming episodes appear here.',
  paused: 'Shows you pause ("watch later") appear here.',
};

function subtitle(item: ShowListItem, bucket: BucketKey): string {
  if (bucket === 'watch_list') {
    if (item.unwatched_count) {
      return `${item.unwatched_count} episode${item.unwatched_count > 1 ? 's' : ''} to watch`;
    }
    const next = formatDate(item.next_airstamp);
    return next ? `Caught up · next episode ${next}` : 'Caught up';
  }
  if (bucket === 'up_next') {
    const next = formatDate(item.next_airstamp);
    return next ? `Next episode: ${next}` : 'Upcoming episodes';
  }
  return item.status;
}

/** Shows tab (spec §3.1): Watch list / Up next / Paused sub-tabs. */
export default function ShowsScreen() {
  const { api } = useAuth();
  const navigation = useNavigation<RootNavigation>();
  const [bucket, setBucket] = useState<BucketKey>('watch_list');
  const { data, error, reload } = useFocusedFetch(useCallback(() => api.myShows(), [api]));

  const togglePause = async (item: ShowListItem) => {
    await api.setSubscriptionStatus(
      'show',
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
            subtitle={subtitle(item, bucket)}
            posterUrl={item.poster_url}
            onPress={() =>
              navigation.navigate('ShowDetail', { showId: item.id, title: item.title })
            }
            actionLabel={bucket === 'paused' ? 'Resume' : 'Pause'}
            onAction={() => togglePause(item)}
          />
        )}
        ListEmptyComponent={
          <EmptyState
            message="No shows tracked yet"
            hint={`${EMPTY_HINTS[bucket]} Find shows in Search and subscribe.`}
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
