import { Platform } from 'react-native';

/**
 * Base URL of the Dockerized backend (docker-compose exposes it on the host
 * at port 8000).
 * - Android emulator reaches the host machine via 10.0.2.2.
 * - iOS simulator shares the host network, so localhost works.
 * - For a physical device, replace this with your machine's LAN IP.
 */
export const API_BASE_URL = Platform.select({
  android: 'http://10.0.2.2:8000',
  default: 'http://localhost:8000',
});

/**
 * The *Web application* OAuth client ID from Google Cloud Console — must be
 * the same client ID the backend verifies against (GOOGLE_OAUTH_CLIENT_ID
 * in the root .env). See README "Google Sign-In setup".
 */
export const GOOGLE_WEB_CLIENT_ID =
  '819050771849-i6eanottvc5s91iusesbj70sj7gimro8.apps.googleusercontent.com';
