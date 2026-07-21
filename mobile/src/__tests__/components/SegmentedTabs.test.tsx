/* eslint-env jest */
import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react-native';
import SegmentedTabs from '../../components/SegmentedTabs';

const TABS = [
  { key: 'a', label: 'Watch list' },
  { key: 'b', label: 'Up next' },
];

describe('SegmentedTabs', () => {
  it('renders every tab label', () => {
    render(<SegmentedTabs tabs={TABS} selected="a" onSelect={jest.fn()} />);

    expect(screen.getByText('Watch list')).toBeOnTheScreen();
    expect(screen.getByText('Up next')).toBeOnTheScreen();
  });

  it('reports the key of the pressed tab', () => {
    const onSelect = jest.fn();
    render(<SegmentedTabs tabs={TABS} selected="a" onSelect={onSelect} />);

    fireEvent.press(screen.getByText('Up next'));

    expect(onSelect).toHaveBeenCalledWith('b');
  });
});
