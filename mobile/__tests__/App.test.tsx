/**
 * App shell integration: which top-level surface renders for each launch
 * state — restoring, signed-out (Login), and a restored session (Tabs). The
 * token-refresh / silent-recovery mechanics are covered at the unit level in
 * src/__tests__/{api,auth}.test — here we only assert the shell's branching.
 *
 * @format
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react-native';
import App from '../App';
import * as sessionStore from '../src/sessionStore';
import { makeTokens } from '../src/__tests__/helpers/fixtures';

// Drive the launch branch purely through what loadSession resolves to.
jest.mock('../src/sessionStore', () => ({
  ...jest.requireActual('../src/sessionStore'),
  loadSession: jest.fn(),
}));

const loadSession = sessionStore.loadSession as jest.Mock;

afterEach(() => {
  jest.clearAllMocks();
});

describe('App shell', () => {
  it('shows the Login screen when no session is stored', async () => {
    loadSession.mockResolvedValue(null);

    render(<App />);

    await waitFor(() =>
      expect(screen.getByText('Sign in with Google')).toBeOnTheScreen(),
    );
  });

  it('shows the tab shell when a stored session restores', async () => {
    loadSession.mockResolvedValue({ provider: 'google', tokens: makeTokens() });

    render(<App />);

    // The bottom tab bar renders even though the data fetches fail against the
    // disabled network — the shell must not depend on a successful first load.
    await waitFor(() =>
      expect(screen.getAllByText('Profile').length).toBeGreaterThan(0),
    );
    // 'Shows' appears both as the tab label and the stack header title.
    expect(screen.getAllByText('Shows').length).toBeGreaterThan(0);
    // No Login surface once a session is present.
    expect(screen.queryByText('Sign in with Google')).toBeNull();
  });

  it('renders without crashing while the session restore is in flight', async () => {
    // A pending loadSession keeps the app in its restoring (spinner) state.
    loadSession.mockReturnValue(new Promise(() => {}));

    render(<App />);

    expect(screen.queryByText('Sign in with Google')).toBeNull();
    // Let any queued microtasks flush so teardown is clean.
    await waitFor(() => expect(loadSession).toHaveBeenCalled());
  });
});
