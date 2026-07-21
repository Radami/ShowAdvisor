module.exports = {
  preset: '@react-native/jest-preset',
  // Only *.test files are suites — shared helpers/fixtures live under
  // __tests__ too and must not be picked up as (empty) test files.
  testMatch: ['**/*.test.{js,jsx,ts,tsx}'],
  // Same as the preset's default, plus @react-native-google-signin,
  // @react-navigation, @react-native-vector-icons, and react-native-screens
  // (all ship untranspiled ESM that jest must run through babel).
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?|@react-native-async-storage|@react-native-google-signin|@react-native-vector-icons|@react-navigation|react-native-screens)/)',
  ],
  // The preset's transform, plus .ttf: @react-native-vector-icons imports its
  // icon font directly, so jest must treat fonts as assets too.
  transform: {
    '^.+\\.(js|ts|tsx)$': 'babel-jest',
    '^.+\\.(bmp|gif|jpg|jpeg|mp4|png|psd|svg|webp|ttf)$': require.resolve(
      '@react-native/jest-preset/jest/assetFileTransformer.js',
    ),
  },
  setupFiles: [
    './node_modules/@react-native-google-signin/google-signin/jest/build/jest/setup.js',
    './jest.setup.js',
  ],
  // React Native Testing Library's built-in matchers (toBeOnScreen,
  // toHaveTextContent, …). The package ships no exports map, so we point at
  // the built subpath directly.
  setupFilesAfterEnv: [
    '@testing-library/react-native/build/matchers/extend-expect',
  ],
  // Product source only — config, fixtures, and test helpers are excluded so
  // the numbers reflect behavior actually under test.
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/__tests__/**',
    '!src/config.ts',
    '!src/navigation.ts',
    '!src/theme.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
    // The pure-logic core carries the load-bearing error handling, so hold it
    // to a higher bar than the UNSHIPPED-yet screens.
    './src/api.ts': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    './src/sessionStore.ts': {
      branches: 90,
      functions: 100,
      lines: 90,
      statements: 90,
    },
  },
};
