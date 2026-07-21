/* eslint-env jest */
import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react-native';
import TitleRow from '../../components/TitleRow';

describe('TitleRow', () => {
  it('renders title and subtitle and fires onPress', () => {
    const onPress = jest.fn();
    render(
      <TitleRow
        title="The Expanse"
        subtitle="Show · 2015"
        posterUrl={null}
        onPress={onPress}
      />,
    );

    expect(screen.getByText('The Expanse')).toBeOnTheScreen();
    expect(screen.getByText('Show · 2015')).toBeOnTheScreen();

    fireEvent.press(screen.getByText('The Expanse'));
    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it('omits the subtitle line when none is given', () => {
    render(<TitleRow title="Dune" posterUrl={null} onPress={jest.fn()} />);

    expect(screen.queryByText('Show · 2015')).toBeNull();
  });

  it('renders the inline action only when both label and handler are supplied', () => {
    const onAction = jest.fn();
    render(
      <TitleRow
        title="Dune"
        posterUrl={null}
        onPress={jest.fn()}
        actionLabel="Pause"
        onAction={onAction}
      />,
    );

    fireEvent.press(screen.getByText('Pause'));
    expect(onAction).toHaveBeenCalledTimes(1);
  });

  it('renders no action when the label is missing', () => {
    render(<TitleRow title="Dune" posterUrl={null} onPress={jest.fn()} />);

    expect(screen.queryByText('Pause')).toBeNull();
  });
});
