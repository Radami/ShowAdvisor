import React from 'react';
import { Pressable, StyleSheet, Text } from 'react-native';
import { SubscriptionStatus } from '../api';
import { colors } from '../theme';

const ACTIVE: SubscriptionStatus = 'active';
const PAUSED: SubscriptionStatus = 'paused';

type Subscription = { status: SubscriptionStatus } | null;

/**
 * Subscribe / Pause-Resume / Unsubscribe controls shared by the Show and
 * Movie detail screens. The caller owns layout (it wraps these in its own
 * row) and receives the target subscription state through `onChange`.
 */
export default function SubscriptionActions({
  subscription,
  onChange,
}: {
  subscription: Subscription;
  onChange: (subscription: Subscription) => void;
}) {
  // Not subscribed yet — one primary call to action.
  if (!subscription) {
    return (
      <ActionButton label="Subscribe" primary onPress={() => onChange({ status: ACTIVE })} />
    );
  }

  // Subscribed — offer pause ("watch later") / resume plus unsubscribe.
  const paused = subscription.status === PAUSED;

  return (
    <>
      <ActionButton
        label={paused ? 'Resume' : 'Pause'}
        onPress={() => onChange({ status: paused ? ACTIVE : PAUSED })}
      />
      <ActionButton label="Unsubscribe" onPress={() => onChange(null)} />
    </>
  );
}

function ActionButton({
  label,
  onPress,
  primary,
}: {
  label: string;
  onPress: () => void;
  primary?: boolean;
}) {
  return (
    <Pressable style={[styles.button, primary && styles.buttonPrimary]} onPress={onPress}>
      <Text style={[styles.buttonText, primary && styles.buttonTextPrimary]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
    backgroundColor: colors.surface,
  },
  buttonPrimary: {
    backgroundColor: colors.accent,
  },
  buttonText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.accent,
  },
  buttonTextPrimary: {
    color: '#fff',
  },
});
