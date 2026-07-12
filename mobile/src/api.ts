import { API_BASE_URL } from './config';

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface Profile {
  username: string;
  email: string;
}

export type SubscriptionStatus = 'active' | 'paused';

export interface SearchResult {
  type: 'show' | 'movie';
  id: number;
  title: string;
  year: number | null;
  poster_url: string | null;
  status?: string;
  release_date?: string | null;
}

export interface EpisodeDetail {
  id: number;
  episode_number: number | null;
  title: string;
  overview: string;
  air_date: string | null;
  airstamp: string | null;
  runtime: number | null;
  watched: boolean;
}

export interface SeasonDetail {
  id: number;
  season_number: number;
  episodes: EpisodeDetail[];
}

export interface ShowDetail {
  id: number;
  title: string;
  status: string;
  premiered: string | null;
  ended: string | null;
  summary: string;
  runtime: number | null;
  network: string;
  poster_url: string | null;
  subscription: { status: SubscriptionStatus } | null;
  seasons: SeasonDetail[];
}

export interface MovieDetail {
  id: number;
  title: string;
  release_date: string | null;
  runtime: number | null;
  summary: string;
  poster_url: string | null;
  subscription: { status: SubscriptionStatus } | null;
  watched: boolean;
}

export interface ShowListItem {
  id: number;
  title: string;
  status: string;
  poster_url: string | null;
  subscription_status: SubscriptionStatus;
  unwatched_count?: number;
  next_airstamp?: string | null;
}

export interface MovieListItem {
  id: number;
  title: string;
  release_date: string | null;
  poster_url: string | null;
  subscription_status: SubscriptionStatus;
}

export interface Buckets<T> {
  watch_list: T[];
  up_next: T[];
  paused: T[];
}

export interface HistoryItem {
  type: 'episode' | 'movie';
  watched_at: string;
  title: string;
  show_id?: number;
  show_title?: string;
  season_number?: number;
  episode_number?: number | null;
  episode_id?: number;
  movie_id?: number;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

/**
 * Exchange a Google ID token for the app's own JWT pair (backend
 * /api/auth/google/, spec §5 Auth).
 */
export async function loginWithGoogle(idToken: string): Promise<AuthTokens> {
  const response = await fetch(`${API_BASE_URL}/api/auth/google/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_token: idToken }),
  });
  if (!response.ok) {
    throw new ApiError(
      response.status,
      `Login failed (${response.status}): ${await response.text()}`,
    );
  }
  const data = await response.json();
  return { access: data.access, refresh: data.refresh };
}

/**
 * Authenticated API client. `onUnauthorized` fires on any 401 (expired
 * access token) so the app can drop back to the Login screen — real token
 * refresh arrives with Milestone 2.2.
 */
export class Api {
  constructor(
    private accessToken: string,
    private onUnauthorized: () => void,
  ) {}

  private async request<T>(
    path: string,
    method: 'GET' | 'POST' | 'PATCH' | 'DELETE' = 'GET',
    body?: object,
  ): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${this.accessToken}`,
        ...(body ? { 'Content-Type': 'application/json' } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (response.status === 401) {
      this.onUnauthorized();
      throw new ApiError(401, 'Session expired — please sign in again.');
    }
    if (!response.ok) {
      throw new ApiError(
        response.status,
        `${method} ${path} failed (${response.status})`,
      );
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return response.json();
  }

  getProfile(): Promise<Profile> {
    return this.request('/api/profile/');
  }

  search(query: string): Promise<{ query: string; results: SearchResult[] }> {
    return this.request(`/api/search/?q=${encodeURIComponent(query)}`);
  }

  getShow(id: number): Promise<ShowDetail> {
    return this.request(`/api/shows/${id}/`);
  }

  getMovie(id: number): Promise<MovieDetail> {
    return this.request(`/api/movies/${id}/`);
  }

  setEpisodeWatched(id: number, watched: boolean): Promise<void> {
    return this.request(`/api/episodes/${id}/watched/`, watched ? 'POST' : 'DELETE');
  }

  setSeasonWatched(id: number, watched: boolean): Promise<void> {
    return this.request(`/api/seasons/${id}/watched/`, watched ? 'POST' : 'DELETE');
  }

  setMovieWatched(id: number, watched: boolean): Promise<void> {
    return this.request(`/api/movies/${id}/watched/`, watched ? 'POST' : 'DELETE');
  }

  subscribe(type: 'show' | 'movie', id: number): Promise<{ status: SubscriptionStatus }> {
    return this.request(`/api/${type}s/${id}/subscription/`, 'POST');
  }

  unsubscribe(type: 'show' | 'movie', id: number): Promise<void> {
    return this.request(`/api/${type}s/${id}/subscription/`, 'DELETE');
  }

  setSubscriptionStatus(
    type: 'show' | 'movie',
    id: number,
    status: SubscriptionStatus,
  ): Promise<{ status: SubscriptionStatus }> {
    return this.request(`/api/${type}s/${id}/subscription/`, 'PATCH', { status });
  }

  myShows(): Promise<Buckets<ShowListItem>> {
    return this.request('/api/my/shows/');
  }

  myMovies(): Promise<Buckets<MovieListItem>> {
    return this.request('/api/my/movies/');
  }

  history(): Promise<{ history: HistoryItem[] }> {
    return this.request('/api/history/');
  }
}
