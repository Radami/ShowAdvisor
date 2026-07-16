import React, { useState } from 'react';
import { ActivityIndicator, Alert, FlatList, StyleSheet, Text, View } from 'react-native';
import { useAuth } from '../auth';
import { Buckets, EntityKind, SubscriptionStatus } from '../api';
import { colors } from '../theme';
import { useFocusedFetch } from '../hooks';
import EmptyState from './EmptyState';
import SegmentedTabs from './SegmentedTabs';
import TitleRow from './TitleRow';

// The three sub-tabs (spec §3.1). Kept as a const map rather than loose
// strings so callers reference Bucket.WatchList instead of 'watch_list'.
export const Bucket = {
  WatchList: 'watch_list',
  UpNext: 'up_next',
  Paused: 'paused',
} as const;

export type BucketKey = (typeof Bucket)[keyof typeof Bucket];

const TABS: { key: BucketKey; label: string }[] = [
  { key: Bucket.WatchList, label: 'Watch list' },
  { key: Bucket.UpNext, label: 'Up next' },
  { key: Bucket.Paused, label: 'Paused' },
];

const ACTIVE: SubscriptionStatus = 'active';
const PAUSED: SubscriptionStatus = 'paused';

// The minimal row shape the list needs; ShowListItem and MovieListItem
// both satisfy it, which is what lets one screen serve both tabs.
interface ListEntity {
  id: number;
  title: string;
  poster_url: string | null;
  subscription_status: SubscriptionStatus;
}

/**
 * Shared Watch list / Up next / Paused list screen for the Shows and Movies
 * tabs (spec §3.1). Callers supply the fetch, the per-bucket subtitle, and
 * the copy/navigation that differ between the two entities.
 */
export default function BucketListScreen<T extends ListEntity>({
  entity,
  fetch,
  subtitle,
  emptyHints,
  emptyMessage,
  emptyCta,
  onOpen,
}: {
  entity: EntityKind;
  fetch: () => Promise<Buckets<T>>;
  // Row subtitle. Receives the active bucket for callers that vary by tab
  // (shows); callers that don't (movies) may ignore it.
  subtitle: (item: T, bucket: BucketKey) => string;
  emptyHints: Record<BucketKey, string>;
  emptyMessage: string;
  emptyCta: string;
  onOpen: (item: T) => void;
}) {
  const { api } = useAuth();
  const [bucket, setBucket] = useState<BucketKey>(Bucket.WatchList);
  const { data, error, reload } = useFocusedFetch(fetch);

  // Pause/resume straight from the list. On failure we reload to snap the row
  // back to server truth and tell the user, rather than leaving it silently
  // wrong with an unhandled rejection behind it.
  const togglePause = async (item: T) => {
    const next = item.subscription_status === PAUSED ? ACTIVE : PAUSED;

    try {
      await api.setSubscriptionStatus(entity, item.id, next);
      reload();
    } catch (e) {
      reload();
      Alert.alert('Could not update', e instanceof Error ? e.message : String(e));
    }
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
            onPress={() => onOpen(item)}
            actionLabel={bucket === Bucket.Paused ? 'Resume' : 'Pause'}
            onAction={() => togglePause(item)}
          />
        )}
        ListEmptyComponent={
          <EmptyState message={emptyMessage} hint={`${emptyHints[bucket]} ${emptyCta}`} />
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
