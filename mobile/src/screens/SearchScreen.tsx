import React, { useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../auth';
import { SearchResult } from '../api';
import { RootNavigation } from '../navigation';
import { colors } from '../theme';
import EmptyState from '../components/EmptyState';
import TitleRow from '../components/TitleRow';

/**
 * Search tab (spec §3.1): title search, no autosuggestions in v1. A miss on
 * the local catalog makes the backend hit the providers live (Tier 3), so
 * the spinner can run a moment longer on brand-new titles.
 */
export default function SearchScreen() {
  const { api } = useAuth();
  const navigation = useNavigation<RootNavigation>();
  const [query, setQuery] = useState('');
  const [searched, setSearched] = useState<string | null>(null);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runSearch = async () => {
    const term = query.trim();
    if (!term || busy) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const data = await api.search(term);
      setResults(data.results);
      setSearched(term);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const openResult = (item: SearchResult) => {
    if (item.type === 'show') {
      navigation.navigate('ShowDetail', { showId: item.id, title: item.title });
    } else {
      navigation.navigate('MovieDetail', { movieId: item.id, title: item.title });
    }
  };

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.input}
        placeholder="Search shows and movies…"
        placeholderTextColor={colors.textMuted}
        value={query}
        onChangeText={setQuery}
        onSubmitEditing={runSearch}
        returnKeyType="search"
        autoCorrect={false}
      />
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {busy ? (
        <ActivityIndicator style={styles.spinner} size="large" />
      ) : (
        <FlatList
          data={results}
          keyExtractor={item => `${item.type}-${item.id}`}
          renderItem={({ item }) => (
            <TitleRow
              title={item.title}
              subtitle={[
                item.type === 'show' ? 'Show' : 'Movie',
                item.year ?? undefined,
              ]
                .filter(Boolean)
                .join(' · ')}
              posterUrl={item.poster_url}
              onPress={() => openResult(item)}
            />
          )}
          ListEmptyComponent={
            searched !== null ? (
              <EmptyState message={`No matches for “${searched}”`} />
            ) : null
          }
          contentContainerStyle={results.length === 0 ? styles.emptyFill : undefined}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  input: {
    margin: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 10,
    backgroundColor: colors.surface,
    fontSize: 16,
    color: colors.text,
  },
  spinner: {
    marginTop: 32,
  },
  error: {
    color: colors.danger,
    textAlign: 'center',
    marginHorizontal: 16,
    marginBottom: 8,
  },
  emptyFill: {
    flexGrow: 1,
  },
});
