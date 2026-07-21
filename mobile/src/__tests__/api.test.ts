/* eslint-env jest */
import { Api, ApiError, AuthTokens, loginWithGoogle } from '../api';
import { API_BASE_URL } from '../config';
import { bodyOf, mockResponse, scriptFetch } from './helpers/mockFetch';
import { makeProfile, makeTokens } from './helpers/fixtures';

const url = (path: string) => `${API_BASE_URL}${path}`;

// A fresh Api plus the callbacks it drives, so each test can assert on which
// lifecycle hook (rotation vs. hard sign-out) fired.
function makeClient(tokens: AuthTokens = makeTokens()) {
  const onTokensRefreshed = jest.fn();
  const onUnauthorized = jest.fn();
  const api = new Api(tokens, onTokensRefreshed, onUnauthorized);
  return { api, onTokensRefreshed, onUnauthorized };
}

describe('loginWithGoogle', () => {
  it('exchanges an ID token for the JWT pair', async () => {
    const { calls } = scriptFetch([
      mockResponse({ json: { access: 'a', refresh: 'r' } }),
    ]);

    const tokens = await loginWithGoogle('id-token-123');

    expect(tokens).toEqual({ access: 'a', refresh: 'r' });
    const [requestUrl, init] = calls[0];
    expect(requestUrl).toBe(url('/api/auth/google/'));
    expect(init?.method).toBe('POST');
    expect(bodyOf(init)).toEqual({ id_token: 'id-token-123' });
  });

  it('throws ApiError carrying the status and body on rejection', async () => {
    scriptFetch([
      mockResponse({ status: 401, ok: false, text: 'invalid token' }),
    ]);

    await expect(loginWithGoogle('bad')).rejects.toMatchObject({
      status: 401,
    });
  });

  it('surfaces the server body text in the error message', async () => {
    scriptFetch([mockResponse({ status: 400, ok: false, text: 'nope' })]);

    await expect(loginWithGoogle('bad')).rejects.toThrow(/nope/);
  });
});

describe('Api — happy path requests', () => {
  it('sends the bearer token and parses the JSON body', async () => {
    const { calls } = scriptFetch([mockResponse({ json: makeProfile() })]);
    const { api } = makeClient();

    const profile = await api.getProfile();

    expect(profile).toEqual(makeProfile());
    const [requestUrl, init] = calls[0];
    expect(requestUrl).toBe(url('/api/profile/'));
    expect((init?.headers as Record<string, string>).Authorization).toBe(
      'Bearer access-token',
    );
  });

  it('url-encodes the search query', async () => {
    const { calls } = scriptFetch([
      mockResponse({ json: { query: 'a b', results: [] } }),
    ]);
    const { api } = makeClient();

    await api.search('a b/c');

    expect(calls[0][0]).toBe(url('/api/search/?q=a%20b%2Fc'));
  });

  it('maps subscribe to POST on the entity subscription path', async () => {
    const { calls } = scriptFetch([mockResponse({ json: { status: 'active' } })]);
    const { api } = makeClient();

    await api.subscribe('show', 42);

    expect(calls[0][0]).toBe(url('/api/shows/42/subscription/'));
    expect(calls[0][1]?.method).toBe('POST');
  });

  it('maps setEpisodeWatched(false) to DELETE', async () => {
    const { calls } = scriptFetch([mockResponse({ status: 204 })]);
    const { api } = makeClient();

    await api.setEpisodeWatched(7, false);

    expect(calls[0][0]).toBe(url('/api/episodes/7/watched/'));
    expect(calls[0][1]?.method).toBe('DELETE');
  });

  it('returns undefined for a 204 No Content response', async () => {
    scriptFetch([mockResponse({ status: 204 })]);
    const { api } = makeClient();

    await expect(api.unsubscribe('movie', 5)).resolves.toBeUndefined();
  });

  it('PATCHes the target status with a JSON body', async () => {
    const { calls } = scriptFetch([mockResponse({ json: { status: 'paused' } })]);
    const { api } = makeClient();

    await api.setSubscriptionStatus('movie', 9, 'paused');

    expect(calls[0][1]?.method).toBe('PATCH');
    expect(bodyOf(calls[0][1])).toEqual({ status: 'paused' });
  });
});

describe('Api — endpoint mapping', () => {
  // Each remaining delegate: fire it, assert the path + verb it produces. The
  // response body is irrelevant here, so a bare 200 stands in.
  const cases: Array<{
    name: string;
    run: (api: Api) => Promise<unknown>;
    path: string;
    method: string;
  }> = [
    { name: 'getShow', run: a => a.getShow(3), path: '/api/shows/3/', method: 'GET' },
    { name: 'getMovie', run: a => a.getMovie(4), path: '/api/movies/4/', method: 'GET' },
    {
      name: 'setEpisodeWatched(true)',
      run: a => a.setEpisodeWatched(8, true),
      path: '/api/episodes/8/watched/',
      method: 'POST',
    },
    {
      name: 'setSeasonWatched(true)',
      run: a => a.setSeasonWatched(2, true),
      path: '/api/seasons/2/watched/',
      method: 'POST',
    },
    {
      name: 'setSeasonWatched(false)',
      run: a => a.setSeasonWatched(2, false),
      path: '/api/seasons/2/watched/',
      method: 'DELETE',
    },
    {
      name: 'setMovieWatched(true)',
      run: a => a.setMovieWatched(5, true),
      path: '/api/movies/5/watched/',
      method: 'POST',
    },
    {
      name: 'unsubscribe',
      run: a => a.unsubscribe('show', 7),
      path: '/api/shows/7/subscription/',
      method: 'DELETE',
    },
    { name: 'myShows', run: a => a.myShows(), path: '/api/my/shows/', method: 'GET' },
    { name: 'myMovies', run: a => a.myMovies(), path: '/api/my/movies/', method: 'GET' },
    { name: 'history', run: a => a.history(), path: '/api/history/', method: 'GET' },
  ];

  it.each(cases)('$name hits $method $path', async ({ run, path, method }) => {
    const { calls } = scriptFetch([mockResponse({ status: 204 })]);
    const { api } = makeClient();

    await run(api);

    expect(calls[0][0]).toBe(url(path));
    expect(calls[0][1]?.method).toBe(method);
  });
});

describe('Api — error handling', () => {
  it('throws ApiError with status and body for a non-401 failure', async () => {
    scriptFetch([mockResponse({ status: 500, ok: false, text: 'boom' })]);
    const { api } = makeClient();

    const error = await api.getProfile().catch(e => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(500);
    expect(error.message).toContain('boom');
  });

  it('propagates a transport-level rejection instead of hanging', async () => {
    scriptFetch([new Error('network down')]);
    const { api } = makeClient();

    await expect(api.getProfile()).rejects.toThrow('network down');
  });
});

describe('Api — token refresh on 401', () => {
  it('refreshes once, retries, and returns the retried result', async () => {
    const { calls } = scriptFetch([
      mockResponse({ status: 401, ok: false }), // original request
      mockResponse({ json: { access: 'a2', refresh: 'r2' } }), // refresh
      mockResponse({ json: makeProfile() }), // retry
    ]);
    const { api, onTokensRefreshed, onUnauthorized } = makeClient();

    const profile = await api.getProfile();

    expect(profile).toEqual(makeProfile());
    expect(calls[1][0]).toBe(url('/api/auth/token/refresh/'));
    // Retry carries the rotated access token, not the stale one.
    expect((calls[2][1]?.headers as Record<string, string>).Authorization).toBe(
      'Bearer a2',
    );
    expect(onTokensRefreshed).toHaveBeenCalledWith({ access: 'a2', refresh: 'r2' });
    expect(onUnauthorized).not.toHaveBeenCalled();
  });

  it('keeps the old refresh token when the server omits a rotated one', async () => {
    scriptFetch([
      mockResponse({ status: 401, ok: false }),
      mockResponse({ json: { access: 'a2' } }), // no refresh returned
      mockResponse({ json: makeProfile() }),
    ]);
    const { api, onTokensRefreshed } = makeClient(makeTokens({ refresh: 'r1' }));

    await api.getProfile();

    expect(onTokensRefreshed).toHaveBeenCalledWith({ access: 'a2', refresh: 'r1' });
  });

  it('fires onUnauthorized and throws a 401 when refresh is rejected', async () => {
    scriptFetch([
      mockResponse({ status: 401, ok: false }),
      mockResponse({ status: 401, ok: false }), // refresh itself rejected
    ]);
    const { api, onUnauthorized } = makeClient();

    const error = await api.getProfile().catch(e => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(401);
    expect(onUnauthorized).toHaveBeenCalledTimes(1);
  });

  it('treats a refresh transport failure as a failed refresh (no throw leak)', async () => {
    scriptFetch([
      mockResponse({ status: 401, ok: false }),
      new Error('offline'), // refresh network error is swallowed → false
    ]);
    const { api, onUnauthorized } = makeClient();

    await expect(api.getProfile()).rejects.toMatchObject({ status: 401 });
    expect(onUnauthorized).toHaveBeenCalledTimes(1);
  });

  it('does not retry a second time if the retried request also 401s', async () => {
    const { calls } = scriptFetch([
      mockResponse({ status: 401, ok: false }), // original
      mockResponse({ json: { access: 'a2', refresh: 'r2' } }), // refresh ok
      mockResponse({ status: 401, ok: false }), // retry still 401
    ]);
    const { api, onUnauthorized } = makeClient();

    await expect(api.getProfile()).rejects.toMatchObject({ status: 401 });
    // original + refresh + one retry, then it gives up (no infinite loop).
    expect(calls).toHaveLength(3);
    expect(onUnauthorized).toHaveBeenCalledTimes(1);
  });

  it('single-flights concurrent 401s into one refresh call', async () => {
    const { fetch, calls } = scriptFetch([]);

    // Both initial requests 401; the refresh resolves once; both retries pass.
    const responses: Record<string, Response[]> = {
      [url('/api/profile/')]: [
        mockResponse({ status: 401, ok: false }),
        mockResponse({ json: makeProfile() }),
      ],
      [url('/api/my/shows/')]: [
        mockResponse({ status: 401, ok: false }),
        mockResponse({ json: { watch_list: [], up_next: [], paused: [] } }),
      ],
      [url('/api/auth/token/refresh/')]: [
        mockResponse({ json: { access: 'a2', refresh: 'r2' } }),
      ],
    };

    fetch.mockImplementation((requestUrl: string) => {
      calls.push([requestUrl, undefined]);
      const next = responses[requestUrl]?.shift();
      return next ? Promise.resolve(next) : Promise.reject(new Error(requestUrl));
    });

    const { api, onTokensRefreshed } = makeClient();

    await Promise.all([api.getProfile(), api.myShows()]);

    const refreshCalls = calls.filter(
      ([u]) => u === url('/api/auth/token/refresh/'),
    );
    expect(refreshCalls).toHaveLength(1);
    expect(onTokensRefreshed).toHaveBeenCalledTimes(1);
  });
});
