# ShowAdvisor — architecture & setup

Deeper documentation for contributors: current build state, repository layout,
one-time configuration (Google Sign-In, TMDB, catalog seeding), and the backend
API surface. For a quick start — running the stack and the tests — see the
[README](README.md).

## Current state

**Core app working end-to-end (Milestones 1, 3.1–3.4, 4.1–4.2, 5, 6).**

- **Backend:** full Phase 1 data model, TVmaze/TMDB sync pipeline (Tier 1 bulk
  seed + Tier 3 on-demand fetch + canonical merge), fuzzy search, detail
  endpoints, and the complete watch-tracking API.
- **Mobile:** real 4-tab app (Search / Shows / Movies / Profile) with Google
  login, show/movie detail screens with watched toggles, Watch list/Up next/Paused
  lists with pause/resume, and Watch History — verified on the Android emulator
  against the dockerized backend. Sessions persist across restarts: stored JWTs
  refresh transparently, and an expired session re-authenticates silently with the
  provider chosen at sign-in — a fresh install prompts for a sign-in method once,
  then never again.

**Next blocks:** remaining auth (Milestone 2 — Facebook/Apple providers,
multi-device confirmation), notifications (7), billing (8), and the deferred
backend stragglers (3.5–3.7, 4.3).

## Repository layout

```
backend/            Django project (single Docker image; run as `web` now, `worker`/`beat` later)
  config/           Settings, root urlconf, Celery app, WSGI/ASGI entry points
  accounts/         Custom User model, Google login, /api/profile/
  catalog/          Shows/movies/episodes, provider clients + sync pipeline, search + detail APIs
  tracking/         Watched state, subscriptions, Watch list/Up next/Paused + history APIs
  notifications/    DeviceToken model (dispatch comes in Milestone 7)
  billing/          UserSubscription/SubscriptionEvent models (lifecycle comes in Milestone 8)
  Dockerfile
  requirements.txt
mobile/             Bare React Native app (Android + iOS, one codebase)
  src/config.ts     API base URL + Google web client ID (edit this)
  src/api.ts        Typed backend API client (auth + token refresh, search, detail, tracking)
  src/auth.tsx      Auth context: provider-aware silent re-auth, transparent refresh
  src/sessionStore.ts AsyncStorage persistence for the session (JWT pair + login provider)
  src/navigation.ts Navigator param types (bottom tabs + native stack)
  src/hooks.ts      Data hooks: focus-refetch + optimistic detail writes
  src/theme.ts      Shared color palette
  src/components/   Shared UI (poster, list row, sub-tabs, empty state, subscribe/pause actions, shared bucket-list screen)
  src/screens/      Login, Search, Shows, Movies, Profile, ShowDetail, MovieDetail, History
  src/__tests__/    Jest suite: helpers/fixtures, api/auth/hooks/session unit tests, component + screen tests
docker-compose.yml  Local dev stack: web + Postgres + Redis
.env.example        Template for required secrets (copy to .env)
```

## Configuration

The backend runs without any of the below (in degraded mode), but sign-in and
movie data need one-time credential setup.

### Google Sign-In (required to log in)

Sign-in is social-login-only. Milestone 0 wires Google; Facebook/Apple
come in Milestone 2. You need OAuth clients in
[Google Cloud Console](https://console.cloud.google.com/) → *APIs & Services* →
*Credentials* (create a project and configure the OAuth consent screen first,
adding your Google account as a test user):

1. **Web application** client — this is the ID the backend validates tokens
   against, *and* the `webClientId` the app requests ID tokens for.
   - Put its client ID and secret in `.env` (`GOOGLE_OAUTH_CLIENT_ID`,
     `GOOGLE_OAUTH_CLIENT_SECRET`), then restart: `docker compose up -d`.
   - Put the same client ID in `mobile/src/config.ts` as `GOOGLE_WEB_CLIENT_ID`.
2. **Android** client — package name `com.showadvisor`, plus the SHA-1 of your
   debug keystore:
   - Linux/macOS: `keytool -list -v -alias androiddebugkey -keystore mobile/android/app/debug.keystore -storepass android | grep SHA1`
   - Windows (PowerShell): `keytool -list -v -alias androiddebugkey -keystore mobile\android\app\debug.keystore -storepass android | Select-String SHA1`
   - No ID goes in the code — registering it in the console is enough.
3. **iOS** client (only when building on a Mac) — bundle ID `com.showadvisor`.

### TMDB API key (needed for movies)

TVmaze (shows, episodes, schedules) needs no key. TMDB (movie catalog +
posters/enhancement for shows) does: create one at
[themoviedb.org/settings/api](https://www.themoviedb.org/settings/api) and put it
in `.env` as `TMDB_API_KEY` (either the v3 API key or the v4 read access token
works), then `docker compose up -d`. Without it the backend runs in degraded
mode — no movie search/detail from providers and no TMDB posters, while all show
functionality works.

### Seed the catalog (optional)

Search works without any seeding — a query that misses the local DB falls back to
a live provider fetch (Tier 3) and caches the result. To pre-populate
the local show index from TVmaze (Tier 1), run the seed task manually (Celery
worker/beat scheduling arrives with plan task 3.6):

```sh
# seed N pages of TVmaze's show index (250 shows/page, ~1 request/page);
# omit max_pages to walk the entire index (~80k shows, takes a while).
docker compose exec web python manage.py shell -c \
  "from catalog.tasks import seed_tvmaze_catalog; print(seed_tvmaze_catalog.apply(kwargs={'max_pages': 20}).get())"
```

The task is resumable — rerunning it picks up from the last synced page. Seeded
records are lightweight (no episodes); a show's full detail (seasons, episodes,
alternate titles, TMDB data) is fetched automatically the first time its detail
endpoint is viewed.

## Verify the walking skeleton (Milestone 0.5 checkpoint)

With the backend up and the Google credentials configured:

1. `docker compose up` from a clean state brings up web + Postgres + Redis with no errors.
2. http://localhost:8000/admin/ loads.
3. Launch the app on the Android emulator (and, on a Mac, the iOS simulator).
4. Tap **Sign in with Google**, complete the flow with a test account.
5. The Profile screen shows the account's real username and email, fetched from
   `/api/profile/` with the JWT issued by the backend.

**Stop and confirm this manually before starting Milestone 1** —
infrastructure problems are far cheaper to fix now.

## API surface

All `/api/` endpoints except the two auth ones require a `Bearer` JWT.

| Endpoint | Methods | Purpose |
|---|---|---|
| `/api/auth/google/` | POST `{"id_token"}` | Exchange a Google ID token for the app's JWT `{access, refresh}` |
| `/api/auth/token/refresh/` | POST `{"refresh"}` | Refresh an expired access token |
| `/api/profile/` | GET | `{username, email}` of the logged-in user |
| `/api/search/?q=…&year=…` | GET | Fuzzy title search across shows + movies (`year` optional); falls back to live provider fetch on miss |
| `/api/shows/<id>/` | GET | Show detail: info, poster, subscription, seasons + episodes with per-user `watched` |
| `/api/movies/<id>/` | GET | Movie detail: info, poster, subscription, `watched` |
| `/api/episodes/<id>/watched/` | POST / DELETE | Mark / unmark an episode watched |
| `/api/seasons/<id>/watched/` | POST / DELETE | Mark / unmark a whole season watched |
| `/api/movies/<id>/watched/` | POST / DELETE | Mark / unmark a movie watched |
| `/api/shows/<id>/subscription/` | POST / PATCH / DELETE | Subscribe / pause-resume (`{"status": "active"\|"paused"}`) / unsubscribe |
| `/api/movies/<id>/subscription/` | POST / PATCH / DELETE | Same, for movies |
| `/api/my/shows/` | GET | `{watch_list, up_next, paused}` buckets |
| `/api/my/movies/` | GET | Same, for movies |
| `/api/history/?limit=N` | GET | Watch history, most recent first |
| `/admin/` | session | Django admin |
