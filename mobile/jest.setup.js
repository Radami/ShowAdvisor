/* eslint-env jest */
// AsyncStorage has no test implementation of its own — use the in-memory
// mock the package ships for jest.
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest'),
);

// No real network from unit tests: Node's global fetch would otherwise fire
// live requests (e.g. the launch-time silent login exchanging an ID token).
global.fetch = jest.fn(() =>
  Promise.reject(new Error('network disabled in tests')),
);
