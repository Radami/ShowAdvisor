/**
 * @format
 */

import React from 'react';
import ReactTestRenderer from 'react-test-renderer';
import App from '../App';

test('renders correctly', async () => {
  // async act: lets the launch-time session restore (loadTokens /
  // trySilentLogin) settle before the test environment tears down.
  await ReactTestRenderer.act(async () => {
    ReactTestRenderer.create(<App />);
  });
});
