import type { NavigatorScreenParams } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

export type TabParamList = {
  Search: undefined;
  Shows: undefined;
  Movies: undefined;
  Profile: undefined;
};

export type RootStackParamList = {
  Tabs: NavigatorScreenParams<TabParamList>;
  ShowDetail: { showId: number; title?: string };
  MovieDetail: { movieId: number; title?: string };
  History: undefined;
};

export type RootNavigation = NativeStackNavigationProp<RootStackParamList>;
