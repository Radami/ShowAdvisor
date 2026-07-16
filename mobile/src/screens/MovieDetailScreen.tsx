import React, { useCallback } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { RouteProp, useRoute } from '@react-navigation/native';
import { useAuth } from '../auth';
import { RootStackParamList } from '../navigation';
import { colors } from '../theme';
import { formatDate, useOptimisticDetail } from '../hooks';
import PosterImage from '../components/PosterImage';
import SubscriptionActions from '../components/SubscriptionActions';

// The movie has a single watched toggle; one key de-dupes rapid taps on it.
const WATCHED_KEY = 'watched';

/**
 * Movie detail screen (spec §3.1): poster/info header, subscribe/pause
 * actions, mark-as-watched action.
 */
export default function MovieDetailScreen() {
  const { api } = useAuth();
  const route = useRoute<RouteProp<RootStackParamList, 'MovieDetail'>>();
  const { movieId } = route.params;

  const fetcher = useCallback(() => api.getMovie(movieId), [api, movieId]);
  const { data: movie, error, mutate, setSubscription } = useOptimisticDetail(
    'movie',
    movieId,
    fetcher,
  );

  const toggleWatched = () =>
    mutate(
      WATCHED_KEY,
      current => ({ ...current, watched: !current.watched }),
      () => api.setMovieWatched(movieId, !movie?.watched),
    );

  if (error) {
    return <Text style={styles.error}>{error}</Text>;
  }
  if (!movie) {
    return <ActivityIndicator style={styles.spinner} size="large" />;
  }

  const released =
    movie.release_date != null && new Date(movie.release_date) <= new Date();
  const releaseText = formatDate(movie.release_date);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.headerTop}>
        <PosterImage url={movie.poster_url} width={110} />
        <View style={styles.headerInfo}>
          <Text style={styles.title}>{movie.title}</Text>
          <Text style={styles.meta}>
            {[
              releaseText
                ? released
                  ? `Released ${releaseText}`
                  : `Releases ${releaseText}`
                : 'Release date TBA',
              movie.runtime ? `${movie.runtime} min` : null,
            ]
              .filter(Boolean)
              .join(' · ')}
          </Text>
        </View>
      </View>

      <Pressable
        style={[styles.watchButton, movie.watched && styles.watchButtonOn]}
        onPress={toggleWatched}>
        <Text style={[styles.watchButtonText, movie.watched && styles.watchButtonTextOn]}>
          {movie.watched ? '✓ Watched' : 'Mark as watched'}
        </Text>
      </Pressable>

      <View style={styles.actions}>
        <SubscriptionActions subscription={movie.subscription} onChange={setSubscription} />
      </View>

      {movie.summary ? <Text style={styles.summary}>{movie.summary}</Text> : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: 16,
    gap: 16,
  },
  spinner: {
    marginTop: 32,
  },
  error: {
    color: colors.danger,
    textAlign: 'center',
    margin: 24,
  },
  headerTop: {
    flexDirection: 'row',
    gap: 16,
  },
  headerInfo: {
    flex: 1,
    gap: 6,
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    color: colors.text,
  },
  meta: {
    fontSize: 14,
    color: colors.textMuted,
  },
  watchButton: {
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    backgroundColor: colors.accent,
  },
  watchButtonOn: {
    backgroundColor: colors.success,
  },
  watchButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  watchButtonTextOn: {
    color: '#fff',
  },
  actions: {
    flexDirection: 'row',
    gap: 8,
  },
  summary: {
    fontSize: 14,
    lineHeight: 20,
    color: colors.text,
  },
});
