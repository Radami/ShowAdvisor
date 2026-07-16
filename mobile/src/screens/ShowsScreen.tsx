import React, { useCallback } from 'react';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../auth';
import { ShowListItem } from '../api';
import { RootNavigation } from '../navigation';
import { formatDate } from '../hooks';
import BucketListScreen, { Bucket, BucketKey } from '../components/BucketListScreen';

const EMPTY_HINTS: Record<BucketKey, string> = {
  watch_list: 'Shows you subscribe to stay here until you’ve watched every episode.',
  up_next: 'Shows with upcoming episodes appear here.',
  paused: 'Shows you pause ("watch later") appear here.',
};

function subtitle(item: ShowListItem, bucket: BucketKey): string {
  // Watch list: how many episodes are still unwatched, else caught-up state.
  if (bucket === Bucket.WatchList) {
    if (item.unwatched_count) {
      return `${item.unwatched_count} episode${item.unwatched_count > 1 ? 's' : ''} to watch`;
    }

    const next = formatDate(item.next_airstamp);
    return next ? `Caught up · next episode ${next}` : 'Caught up';
  }

  // Up next: when the next episode airs.
  if (bucket === Bucket.UpNext) {
    const next = formatDate(item.next_airstamp);
    return next ? `Next episode: ${next}` : 'Upcoming episodes';
  }

  // Paused: label the broadcast status so it reads like the other buckets
  // ("Next episode: …") rather than a bare "Running".
  return item.status ? `Status: ${item.status}` : 'Paused';
}

/** Shows tab (spec §3.1): Watch list / Up next / Paused sub-tabs. */
export default function ShowsScreen() {
  const { api } = useAuth();
  const navigation = useNavigation<RootNavigation>();

  return (
    <BucketListScreen
      entity="show"
      fetch={useCallback(() => api.myShows(), [api])}
      subtitle={subtitle}
      emptyHints={EMPTY_HINTS}
      emptyMessage="No shows tracked yet"
      emptyCta="Find shows in Search and subscribe."
      onOpen={item =>
        navigation.navigate('ShowDetail', { showId: item.id, title: item.title })
      }
    />
  );
}
