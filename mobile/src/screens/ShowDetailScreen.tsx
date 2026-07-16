import React, { useCallback } from 'react';
import {
  ActivityIndicator,
  Pressable,
  SectionList,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { RouteProp, useRoute } from '@react-navigation/native';
import { useAuth } from '../auth';
import { EpisodeDetail } from '../api';
import { RootStackParamList } from '../navigation';
import { colors } from '../theme';
import { formatDate, useOptimisticDetail } from '../hooks';
import PosterImage from '../components/PosterImage';
import SubscriptionActions from '../components/SubscriptionActions';

// Per-target keys so an episode and its season de-dupe independently.
const episodeKey = (id: number) => `episode-${id}`;
const seasonKey = (id: number) => `season-${id}`;

/**
 * Show detail screen (spec §3.1): poster/info header, subscribe/pause
 * actions, season list with a mark-season-watched shortcut, episode list
 * with per-episode watched toggles.
 */
export default function ShowDetailScreen() {
  const { api } = useAuth();
  const route = useRoute<RouteProp<RootStackParamList, 'ShowDetail'>>();
  const { showId } = route.params;

  const fetcher = useCallback(() => api.getShow(showId), [api, showId]);
  const { data: show, error, mutate, setSubscription } = useOptimisticDetail(
    'show',
    showId,
    fetcher,
  );

  const toggleEpisode = (episode: EpisodeDetail) =>
    mutate(
      episodeKey(episode.id),
      current => ({
        ...current,
        seasons: current.seasons.map(season => ({
          ...season,
          episodes: season.episodes.map(e =>
            e.id === episode.id ? { ...e, watched: !episode.watched } : e,
          ),
        })),
      }),
      () => api.setEpisodeWatched(episode.id, !episode.watched),
    );

  const toggleSeason = (seasonId: number, watched: boolean) =>
    mutate(
      seasonKey(seasonId),
      current => ({
        ...current,
        seasons: current.seasons.map(season =>
          season.id === seasonId
            ? { ...season, episodes: season.episodes.map(e => ({ ...e, watched })) }
            : season,
        ),
      }),
      () => api.setSeasonWatched(seasonId, watched),
    );

  if (error) {
    return <Text style={styles.error}>{error}</Text>;
  }
  if (!show) {
    return <ActivityIndicator style={styles.spinner} size="large" />;
  }

  const years = [show.premiered, show.ended]
    .map(d => (d ? d.slice(0, 4) : null))
    .filter(Boolean);
  const yearRange =
    show.status === 'Ended' ? years.join('–') : years[0] ? `${years[0]}–` : '';

  return (
    <SectionList
      style={styles.container}
      sections={show.seasons.map(season => ({
        key: String(season.id),
        seasonId: season.id,
        seasonNumber: season.season_number,
        data: season.episodes,
      }))}
      keyExtractor={episode => String(episode.id)}
      stickySectionHeadersEnabled={false}
      ListHeaderComponent={
        <View style={styles.header}>
          <View style={styles.headerTop}>
            <PosterImage url={show.poster_url} width={100} />
            <View style={styles.headerInfo}>
              <Text style={styles.title}>{show.title}</Text>
              <Text style={styles.meta}>
                {[yearRange, show.status, show.network].filter(Boolean).join(' · ')}
              </Text>
              <View style={styles.actions}>
                <SubscriptionActions
                  subscription={show.subscription}
                  onChange={setSubscription}
                />
              </View>
            </View>
          </View>
          {show.summary ? <Text style={styles.summary}>{show.summary}</Text> : null}
        </View>
      }
      renderSectionHeader={({ section }) => {
        const allWatched =
          section.data.length > 0 && section.data.every(e => e.watched);
        return (
          <View style={styles.seasonHeader}>
            <Text style={styles.seasonTitle}>Season {section.seasonNumber}</Text>
            <Pressable
              onPress={() => toggleSeason(section.seasonId, !allWatched)}
              hitSlop={8}>
              <Text style={styles.seasonAction}>
                {allWatched ? 'Unmark season' : 'Mark season watched'}
              </Text>
            </Pressable>
          </View>
        );
      }}
      renderItem={({ item: episode }) => (
        <Pressable style={styles.episodeRow} onPress={() => toggleEpisode(episode)}>
          <View style={[styles.check, episode.watched && styles.checkOn]}>
            {episode.watched ? <Text style={styles.checkMark}>✓</Text> : null}
          </View>
          <View style={styles.episodeText}>
            <Text style={styles.episodeTitle} numberOfLines={1}>
              {episode.episode_number != null ? `${episode.episode_number}. ` : ''}
              {episode.title || 'Untitled'}
            </Text>
            <Text style={styles.episodeMeta}>
              {formatDate(episode.air_date) ?? 'Air date TBA'}
            </Text>
          </View>
        </Pressable>
      )}
    />
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
  header: {
    padding: 16,
    gap: 12,
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
  actions: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
    flexWrap: 'wrap',
  },
  summary: {
    fontSize: 14,
    lineHeight: 20,
    color: colors.text,
  },
  seasonHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
    backgroundColor: colors.background,
  },
  seasonTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: colors.text,
  },
  seasonAction: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.accent,
  },
  episodeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 12,
  },
  check: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkOn: {
    backgroundColor: colors.success,
    borderColor: colors.success,
  },
  checkMark: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '700',
  },
  episodeText: {
    flex: 1,
    gap: 2,
  },
  episodeTitle: {
    fontSize: 15,
    color: colors.text,
  },
  episodeMeta: {
    fontSize: 12,
    color: colors.textMuted,
  },
});
