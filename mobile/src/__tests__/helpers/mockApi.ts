/* eslint-env jest */
/**
 * A mock standing in for the `Api` client in screen/component tests. Every
 * method is a `jest.fn()` so tests can script resolutions/rejections and
 * assert the exact calls a screen makes — without any real network.
 */
import { Api } from '../../api';

export type MockApi = { [K in keyof Api]: jest.Mock };

/**
 * All methods resolve to `undefined` by default; a test overrides only the
 * ones it exercises, e.g. `api.getShow.mockResolvedValue(makeShowDetail())`.
 */
export function mockApi(): MockApi {
  return {
    getProfile: jest.fn().mockResolvedValue(undefined),
    search: jest.fn().mockResolvedValue({ query: '', results: [] }),
    getShow: jest.fn().mockResolvedValue(undefined),
    getMovie: jest.fn().mockResolvedValue(undefined),
    setEpisodeWatched: jest.fn().mockResolvedValue(undefined),
    setSeasonWatched: jest.fn().mockResolvedValue(undefined),
    setMovieWatched: jest.fn().mockResolvedValue(undefined),
    subscribe: jest.fn().mockResolvedValue({ status: 'active' }),
    unsubscribe: jest.fn().mockResolvedValue(undefined),
    setSubscriptionStatus: jest.fn().mockResolvedValue({ status: 'active' }),
    myShows: jest.fn().mockResolvedValue(undefined),
    myMovies: jest.fn().mockResolvedValue(undefined),
    history: jest.fn().mockResolvedValue(undefined),
  } as unknown as MockApi;
}
