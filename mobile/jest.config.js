module.exports = {
  preset: '@react-native/jest-preset',
  // Same as the preset's default, plus @react-native-google-signin (ships
  // untranspiled ESM that jest must run through babel).
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?|@react-native-google-signin)/)',
  ],
  setupFiles: [
    './node_modules/@react-native-google-signin/google-signin/jest/build/jest/setup.js',
  ],
};
