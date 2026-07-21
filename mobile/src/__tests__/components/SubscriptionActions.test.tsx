/* eslint-env jest */
import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react-native';
import SubscriptionActions from '../../components/SubscriptionActions';

describe('SubscriptionActions', () => {
  it('offers a single Subscribe CTA when not subscribed', () => {
    const onChange = jest.fn();
    render(<SubscriptionActions subscription={null} onChange={onChange} />);

    fireEvent.press(screen.getByText('Subscribe'));

    // Subscribing means an active subscription.
    expect(onChange).toHaveBeenCalledWith({ status: 'active' });
    expect(screen.queryByText('Unsubscribe')).toBeNull();
  });

  it('pauses an active subscription', () => {
    const onChange = jest.fn();
    render(
      <SubscriptionActions subscription={{ status: 'active' }} onChange={onChange} />,
    );

    fireEvent.press(screen.getByText('Pause'));

    expect(onChange).toHaveBeenCalledWith({ status: 'paused' });
  });

  it('resumes a paused subscription', () => {
    const onChange = jest.fn();
    render(
      <SubscriptionActions subscription={{ status: 'paused' }} onChange={onChange} />,
    );

    // A paused subscription shows Resume, not Pause.
    expect(screen.queryByText('Pause')).toBeNull();
    fireEvent.press(screen.getByText('Resume'));

    expect(onChange).toHaveBeenCalledWith({ status: 'active' });
  });

  it('unsubscribes with a null target', () => {
    const onChange = jest.fn();
    render(
      <SubscriptionActions subscription={{ status: 'active' }} onChange={onChange} />,
    );

    fireEvent.press(screen.getByText('Unsubscribe'));

    expect(onChange).toHaveBeenCalledWith(null);
  });
});
