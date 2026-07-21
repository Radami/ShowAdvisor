/**
 * Canonical sample payloads mirroring the backend response shapes in api.ts.
 * Each factory takes an override so a test can tweak just the field it cares
 * about while everything else stays valid.
 */
import {
  AuthTokens,
  Buckets,
  HistoryItem,
  MovieDetail,
  MovieListItem,
  Profile,
  SearchResult,
  ShowDetail,
  ShowListItem,
} from '../../api';

export function makeTokens(overrides: Partial<AuthTokens> = {}): AuthTokens {
  return { access: 'access-token', refresh: 'refresh-token', ...overrides };
}

export function makeProfile(overrides: Partial<Profile> = {}): Profile {
  return { username: 'ada', email: 'ada@example.com', ...overrides };
}

export function makeSearchResult(
  overrides: Partial<SearchResult> = {},
): SearchResult {
  return {
    type: 'show',
    id: 1,
    title: 'The Expanse',
    year: 2015,
    poster_url: 'https://img/expanse.jpg',
    ...overrides,
  };
}

export function makeShowDetail(overrides: Partial<ShowDetail> = {}): ShowDetail {
  return {
    id: 1,
    title: 'The Expanse',
    status: 'Ended',
    premiered: '2015-12-14',
    ended: '2022-01-14',
    summary: 'Belters and inners.',
    runtime: 60,
    network: 'Prime',
    poster_url: 'https://img/expanse.jpg',
    subscription: null,
    seasons: [
      {
        id: 10,
        season_number: 1,
        episodes: [
          {
            id: 100,
            episode_number: 1,
            title: 'Dulcinea',
            overview: '',
            air_date: '2015-12-14',
            airstamp: '2015-12-14T00:00:00Z',
            runtime: 60,
            watched: false,
          },
          {
            id: 101,
            episode_number: 2,
            title: 'The Big Empty',
            overview: '',
            air_date: '2015-12-15',
            airstamp: '2015-12-15T00:00:00Z',
            runtime: 60,
            watched: false,
          },
        ],
      },
    ],
    ...overrides,
  };
}

export function makeMovieDetail(
  overrides: Partial<MovieDetail> = {},
): MovieDetail {
  return {
    id: 5,
    title: 'Dune',
    release_date: '2021-10-22',
    runtime: 155,
    summary: 'Spice.',
    poster_url: 'https://img/dune.jpg',
    subscription: null,
    watched: false,
    ...overrides,
  };
}

export function makeShowListItem(
  overrides: Partial<ShowListItem> = {},
): ShowListItem {
  return {
    id: 1,
    title: 'The Expanse',
    status: 'Ended',
    poster_url: 'https://img/expanse.jpg',
    subscription_status: 'active',
    unwatched_count: 3,
    next_airstamp: null,
    ...overrides,
  };
}

export function makeMovieListItem(
  overrides: Partial<MovieListItem> = {},
): MovieListItem {
  return {
    id: 5,
    title: 'Dune',
    release_date: '2021-10-22',
    poster_url: 'https://img/dune.jpg',
    subscription_status: 'active',
    ...overrides,
  };
}

export function makeShowBuckets(
  overrides: Partial<Buckets<ShowListItem>> = {},
): Buckets<ShowListItem> {
  return {
    watch_list: [makeShowListItem()],
    up_next: [makeShowListItem({ id: 2, title: 'Severance' })],
    paused: [makeShowListItem({ id: 3, title: 'Foundation', subscription_status: 'paused' })],
    ...overrides,
  };
}

export function makeMovieBuckets(
  overrides: Partial<Buckets<MovieListItem>> = {},
): Buckets<MovieListItem> {
  return {
    watch_list: [makeMovieListItem()],
    up_next: [],
    paused: [makeMovieListItem({ id: 6, title: 'Arrival', subscription_status: 'paused' })],
    ...overrides,
  };
}

export function makeHistory(): HistoryItem[] {
  return [
    {
      type: 'episode',
      watched_at: '2026-07-01T12:00:00Z',
      title: 'Dulcinea',
      show_id: 1,
      show_title: 'The Expanse',
      season_number: 1,
      episode_number: 1,
      episode_id: 100,
    },
    {
      type: 'movie',
      watched_at: '2026-07-02T12:00:00Z',
      title: 'Dune',
      movie_id: 5,
    },
  ];
}
