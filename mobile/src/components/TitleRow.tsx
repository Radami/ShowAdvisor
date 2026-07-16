import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors } from '../theme';
import PosterImage from './PosterImage';

/**
 * One row in a vertical title list (spec §3.1: poster, title, status
 * subtitle), with an optional inline action (e.g. Pause/Resume).
 */
export default function TitleRow({
  title,
  subtitle,
  posterUrl,
  onPress,
  actionLabel,
  onAction,
}: {
  title: string;
  subtitle?: string | null;
  posterUrl: string | null | undefined;
  onPress: () => void;
  actionLabel?: string;
  onAction?: () => void;
}) {
  return (
    <Pressable style={styles.row} onPress={onPress}>
      <PosterImage url={posterUrl} />
      <View style={styles.textBlock}>
        <Text style={styles.title} numberOfLines={2}>
          {title}
        </Text>
        {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}
      </View>
      {actionLabel && onAction ? (
        <Pressable style={styles.action} onPress={onAction} hitSlop={8}>
          <Text style={styles.actionText}>{actionLabel}</Text>
        </Pressable>
      ) : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 12,
  },
  textBlock: {
    flex: 1,
    gap: 2,
  },
  title: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text,
  },
  subtitle: {
    fontSize: 13,
    color: colors.textMuted,
  },
  action: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    backgroundColor: colors.surface,
  },
  actionText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.accent,
  },
});
