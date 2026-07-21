/* eslint-env jest */
import React from 'react';
import { render, screen } from '@testing-library/react-native';
import EmptyState from '../../components/EmptyState';

describe('EmptyState', () => {
  it('shows the message and hint', () => {
    render(<EmptyState message="Nothing here" hint="Add something" />);

    expect(screen.getByText('Nothing here')).toBeOnTheScreen();
    expect(screen.getByText('Add something')).toBeOnTheScreen();
  });

  it('omits the hint line when not provided', () => {
    render(<EmptyState message="Nothing here" />);

    expect(screen.getByText('Nothing here')).toBeOnTheScreen();
    expect(screen.queryByText('Add something')).toBeNull();
  });
});
