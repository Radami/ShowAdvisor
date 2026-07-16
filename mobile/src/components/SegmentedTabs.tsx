import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors } from '../theme';

/** The Watching / Up next / Paused sub-tab switcher (spec §3.1). */
export default function SegmentedTabs<T extends string>({
  tabs,
  selected,
  onSelect,
}: {
  tabs: { key: T; label: string }[];
  selected: T;
  onSelect: (key: T) => void;
}) {
  return (
    <View style={styles.container}>
      {tabs.map(tab => (
        <Pressable
          key={tab.key}
          style={[styles.tab, selected === tab.key && styles.tabSelected]}
          onPress={() => onSelect(tab.key)}>
          <Text
            style={[
              styles.label,
              selected === tab.key && styles.labelSelected,
            ]}>
            {tab.label}
          </Text>
        </Pressable>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    margin: 12,
    backgroundColor: colors.surface,
    borderRadius: 8,
    padding: 3,
  },
  tab: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 6,
    alignItems: 'center',
  },
  tabSelected: {
    backgroundColor: colors.background,
    elevation: 1,
  },
  label: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.textMuted,
  },
  labelSelected: {
    color: colors.text,
  },
});
