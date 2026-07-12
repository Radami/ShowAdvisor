module.exports = {
  preset: '@react-native/jest-preset',
  // Same as the preset's default, plus @react-native-google-signin,
  // @react-navigation, @react-native-vector-icons, and react-native-screens
  // (all ship untranspiled ESM that jest must run through babel).
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?|@react-native-google-signin|@react-native-vector-icons|@react-navigation|react-native-screens)/)',
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
  ],
};
