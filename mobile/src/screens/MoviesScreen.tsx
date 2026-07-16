import React, { useCallback } from 'react';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../auth';
import { MovieListItem } from '../api';
import { RootNavigation } from '../navigation';
import { formatDate } from '../hooks';
import BucketListScreen, { BucketKey } from '../components/BucketListScreen';

const EMPTY_HINTS: Record<BucketKey, string> = {
  watch_list: 'Movies you subscribe to stay here until you’ve watched them.',
  up_next: 'Movies you track that aren’t released yet appear here.',
  paused: 'Movies you pause ("watch later") appear here.',
};

function subtitle(item: MovieListItem): string {
  if (!item.release_date) {
    return 'Release date TBA';
  }

  const label = formatDate(item.release_date);
  if (!label) {
    return 'Release date TBA'; // present but unparseable
  }

  // release_date is an ISO date, so a lexical compare against today (also ISO)
  // tells released from upcoming without parsing a second Date.
  const released = item.release_date <= new Date().toISOString().slice(0, 10);
  return released ? `Released ${label}` : `Releases ${label}`;
}

/** Movies tab (spec §3.1) — same three-bucket pattern as Shows. */
export default function MoviesScreen() {
  const { api } = useAuth();
  const navigation = useNavigation<RootNavigation>();

  return (
    <BucketListScreen
      entity="movie"
      fetch={useCallback(() => api.myMovies(), [api])}
      subtitle={subtitle}
      emptyHints={EMPTY_HINTS}
      emptyMessage="No movies tracked yet"
      emptyCta="Find movies in Search and subscribe."
      onOpen={item =>
        navigation.navigate('MovieDetail', { movieId: item.id, title: item.title })
      }
    />
  );
}
