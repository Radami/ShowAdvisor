/* eslint-env jest */
/**
 * Mounts a screen the way the app does — inside a navigator and an auth
 * context — but with a mock Api and no network. This gives real
 * `useNavigation`, `useRoute`, and `useFocusEffect` behavior (so focus-refetch
 * hooks actually fire) while keeping the test hermetic.
 */
import React from 'react';
import { render, RenderOptions } from '@testing-library/react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { AuthContext } from '../../auth';
import { MockApi, mockApi } from './mockApi';

// Static insets/frame so SafeAreaProvider resolves synchronously in tests
// instead of waiting on a native measurement that never arrives.
const SAFE_AREA_METRICS = {
  frame: { x: 0, y: 0, width: 390, height: 844 },
  insets: { top: 47, left: 0, right: 0, bottom: 34 },
};

const Stack = createNativeStackNavigator();

const SCREEN_NAME = 'Target';

interface RenderScreenOptions {
  api?: MockApi;
  signOut?: jest.Mock;
  /** Route params handed to the screen via `useRoute()`. */
  params?: object;
  renderOptions?: Omit<RenderOptions, 'wrapper'>;
}

/**
 * Render `Component` as the single screen of a native stack. Returns the RNTL
 * result plus the `api`/`signOut` mocks so the test can assert on them.
 */
export function renderScreen(
  Component: React.ComponentType<object>,
  options: RenderScreenOptions = {},
) {
  const api = options.api ?? mockApi();
  const signOut = options.signOut ?? jest.fn();

  const utils = render(
    <SafeAreaProvider initialMetrics={SAFE_AREA_METRICS}>
      <AuthContext.Provider value={{ api: api as never, signOut }}>
        <NavigationContainer>
          <Stack.Navigator>
            <Stack.Screen
              name={SCREEN_NAME}
              component={Component}
              initialParams={options.params}
            />
          </Stack.Navigator>
        </NavigationContainer>
      </AuthContext.Provider>
    </SafeAreaProvider>,
    options.renderOptions,
  );

  return { ...utils, api, signOut };
}
