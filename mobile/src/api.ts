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

/** The two subscribable catalog entities, as used in subscription API paths. */
export type EntityKind = 'show' | 'movie';

export interface SearchResult {
  type: EntityKind;
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
 * Authenticated API client (token refresh: Milestone 2.2). A 401 triggers
 * one transparent refresh via /api/auth/token/refresh/ and a retry;
 * `onTokensRefreshed` lets the app persist the rotated pair. Only when the
 * refresh token itself is rejected does `onUnauthorized` fire and drop the
 * app back to the Login screen.
 */
export class Api {
  private refreshing: Promise<boolean> | null = null;

  constructor(
    private tokens: AuthTokens,
    private onTokensRefreshed: (tokens: AuthTokens) => void,
    private onUnauthorized: () => void,
  ) {}

  private async request<T>(
    path: string,
    method: 'GET' | 'POST' | 'PATCH' | 'DELETE' = 'GET',
    body?: object,
    retried = false,
  ): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${this.tokens.access}`,
        ...(body ? { 'Content-Type': 'application/json' } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (response.status === 401) {
      if (!retried && (await this.refresh())) {
        return this.request(path, method, body, true);
      }
      this.onUnauthorized();
      throw new ApiError(401, 'Session expired — please sign in again.');
    }
    if (!response.ok) {
      // Include the body so backend validation errors are legible on-device,
      // matching how loginWithGoogle surfaces failures.
      const errorBody = await response.text();
      throw new ApiError(
        response.status,
        `${method} ${path} failed (${response.status})${errorBody ? `: ${errorBody}` : ''}`,
      );
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return response.json();
  }

  /** Single-flight: concurrent 401s all await the same refresh call. */
  private refresh(): Promise<boolean> {
    this.refreshing ??= (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/auth/token/refresh/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh: this.tokens.refresh }),
        });
        if (!response.ok) {
          return false;
        }
        const data = await response.json();
        // ROTATE_REFRESH_TOKENS is on server-side, so a new refresh token
        // normally comes back alongside the access token.
        this.tokens = {
          access: data.access,
          refresh: data.refresh ?? this.tokens.refresh,
        };
        this.onTokensRefreshed(this.tokens);
        return true;
      } catch {
        return false;
      } finally {
        this.refreshing = null;
      }
    })();
    return this.refreshing;
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

  subscribe(type: EntityKind, id: number): Promise<{ status: SubscriptionStatus }> {
    return this.request(`/api/${type}s/${id}/subscription/`, 'POST');
  }

  unsubscribe(type: EntityKind, id: number): Promise<void> {
    return this.request(`/api/${type}s/${id}/subscription/`, 'DELETE');
  }

  setSubscriptionStatus(
    type: EntityKind,
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
