/* eslint-env jest */
/**
 * Fetch scripting for the API-layer tests.
 *
 * `jest.setup.js` deliberately points `global.fetch` at a rejecting stub so no
 * test hits the network by accident. These helpers install a *scripted* fetch
 * for a single test: each expected call is queued in order, so a token-refresh
 * flow (401 → refresh → retry) can be described as three sequential responses.
 */

interface MockResponseInit {
  status?: number;
  /** JSON body returned by `response.json()`. */
  json?: unknown;
  /** Raw body returned by `response.text()` (error paths read this). */
  text?: string;
  /** Force `response.ok` independently of the status, for edge cases. */
  ok?: boolean;
}

const HTTP_OK_FLOOR = 200;
const HTTP_OK_CEIL = 300;

/** A minimal stand-in for the parts of `Response` the API client touches. */
export function mockResponse(init: MockResponseInit = {}): Response {
  const status = init.status ?? HTTP_OK_FLOOR;
  const ok = init.ok ?? (status >= HTTP_OK_FLOOR && status < HTTP_OK_CEIL);

  return {
    ok,
    status,
    json: async () => init.json,
    text: async () => init.text ?? '',
  } as Response;
}

/** The scripted fetch plus the recorded calls, handed back for assertions. */
export interface ScriptedFetch {
  fetch: jest.Mock;
  /** [url, init] tuples in call order. */
  calls: Array<[string, RequestInit | undefined]>;
}

/**
 * Install a fetch that returns the queued responses in order. A queued
 * `Error` is thrown instead of resolved, to model a transport failure (DNS,
 * offline). Running past the end of the queue is a test bug and throws loudly.
 */
export function scriptFetch(responses: Array<Response | Error>): ScriptedFetch {
  const queue = [...responses];
  const calls: Array<[string, RequestInit | undefined]> = [];

  const fetchMock = jest.fn((url: string, init?: RequestInit) => {
    calls.push([url, init]);

    const next = queue.shift();
    if (next === undefined) {
      throw new Error(`Unexpected fetch call to ${url} — no response queued`);
    }
    if (next instanceof Error) {
      return Promise.reject(next);
    }

    return Promise.resolve(next);
  });

  (globalThis.fetch as unknown) = fetchMock;
  return { fetch: fetchMock, calls };
}

/** Parse the JSON body a recorded call sent, for request-shape assertions. */
export function bodyOf(init: RequestInit | undefined): unknown {
  if (!init?.body) {
    return undefined;
  }
  return JSON.parse(init.body as string);
}
