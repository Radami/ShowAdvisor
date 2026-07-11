import { API_BASE_URL } from './config';

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface Profile {
  username: string;
  email: string;
}

/**
 * Exchange a Google ID token for the app's own JWT pair (backend
 * /api/auth/google/, spec §5 Auth).
 */
export async function loginWithGoogle(idToken: string): Promise<AuthTokens> {
  const response = await fetch(`${API_BASE_URL}/api/auth/google/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_token: idToken }),
  });
  if (!response.ok) {
    throw new Error(`Login failed (${response.status}): ${await response.text()}`);
  }
  const data = await response.json();
  return { access: data.access, refresh: data.refresh };
}

export async function fetchProfile(accessToken: string): Promise<Profile> {
  const response = await fetch(`${API_BASE_URL}/api/profile/`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) {
    throw new Error(`Profile fetch failed (${response.status})`);
  }
  return response.json();
}
