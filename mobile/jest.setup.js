/* eslint-env jest */
// AsyncStorage has no test implementation of its own — use the in-memory
// mock the package ships for jest.
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest'),
);

// SafeAreaProvider normally withholds its children until a native layout
// event supplies insets — which never fires under jest, leaving the tree
// empty. This inline stand-in renders children immediately with static
// insets so full-app renders actually mount their screens. (The library
// ships its own mock, but as untranspiled TSX we'd have to widen
// transformIgnorePatterns to load it.)
jest.mock('react-native-safe-area-context', () => {
  const React = require('react');
  const insets = { top: 0, left: 0, right: 0, bottom: 0 };
  const frame = { x: 0, y: 0, width: 320, height: 640 };
  const passthrough = ({ children }) => React.createElement(React.Fragment, null, children);
  return {
    SafeAreaProvider: passthrough,
    SafeAreaView: passthrough,
    SafeAreaInsetsContext: React.createContext(insets),
    useSafeAreaInsets: () => insets,
    useSafeAreaFrame: () => frame,
    initialWindowMetrics: { insets, frame },
  };
});

// No real network from unit tests: Node's global fetch would otherwise fire
// live requests (e.g. the launch-time silent login exchanging an ID token).
global.fetch = jest.fn(() =>
  Promise.reject(new Error('network disabled in tests')),
);
