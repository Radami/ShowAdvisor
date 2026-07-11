# ShowAdvisor

A self-owned movie & TV series tracker (TV Time replacement): track what you've watched, subscribe to shows and movies, and get notified about upcoming episodes and releases.

- **Design spec:** [`tracker-app-spec.md`](tracker-app-spec.md) — what the product is and how it's built.
- **Implementation plan:** [`tracker-app-implementation-plan.md`](tracker-app-implementation-plan.md) — build order with per-task acceptance criteria.

**Current state: Milestone 0 (walking skeleton).** The stack is Django + DRF + PostgreSQL + Redis in Docker, JWT auth with Google Sign-In, and a bare React Native app with two screens (Login → Profile). It exists to prove every layer talks to every other layer before real features are built on top.

## Repository layout

```
backend/            Django project (single Docker image; run as `web` now, `worker`/`beat` later)
  config/           Settings, root urlconf, WSGI/ASGI entry points
  accounts/         Custom User model, Google login, /api/profile/
  Dockerfile
  requirements.txt
mobile/             Bare React Native app (Android + iOS, one codebase)
  src/config.ts     API base URL + Google web client ID (edit this)
  src/api.ts        Backend API calls
  src/screens/      Login and Profile screens
docker-compose.yml  Local dev stack: web + Postgres + Redis
.env.example        Template for required secrets (copy to .env)
```

## Prerequisites

| Tool | Linux | Windows |
|---|---|---|
| Docker + Compose | [Docker Engine](https://docs.docker.com/engine/install/) or Docker Desktop | [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) with the WSL 2 backend |
| Node.js ≥ 20 + npm | via [nvm](https://github.com/nvm-sh/nvm) or distro packages | via [nvm-windows](https://github.com/coreybutler/nvm-windows) or the installer |
| JDK 17–20 | distro packages (e.g. `openjdk-17-jdk`) | [Temurin 17](https://adoptium.net/) |
| Android Studio + SDK + an emulator (AVD) | [reactnative.dev environment setup](https://reactnative.dev/docs/set-up-your-environment) | same guide, Windows tab |
| Xcode (iOS builds only) | — not possible on Linux | — not possible on Windows; needs a Mac |

> iOS can only be built on macOS. On Linux and Windows, develop against the Android emulator; the same JS codebase runs on iOS unchanged when built from a Mac.

## 1. Run the backend (Docker)

Works identically on Linux (any shell) and Windows (PowerShell or CMD, with Docker Desktop running).

```sh
# from the repo root
cp .env.example .env        # Windows CMD: copy .env.example .env  (PowerShell: cp works)
docker compose up --build
```

That starts three containers: Django (`web`, http://localhost:8000), PostgreSQL, and Redis. Migrations run automatically on startup. The backend code in `backend/` is bind-mounted with auto-reload, so edits apply without rebuilding.

Verify it's up:

- http://localhost:8000/admin/ shows the Django admin login page (proves Django ↔ Postgres works).
- `curl http://localhost:8000/api/profile/` returns `{"detail":"Authentication credentials were not provided."}` with HTTP 401 (proves DRF + JWT auth is wired).

To browse the admin, create a superuser (in a second terminal, while the stack is running):

```sh
docker compose exec web python manage.py createsuperuser
```

Useful commands:

```sh
docker compose up -d          # run in the background
docker compose logs -f web    # follow Django logs
docker compose down           # stop everything (data survives in a named volume)
docker compose down -v        # stop AND wipe the database
```

## 2. Google Sign-In setup (one-time)

Sign-in is social-login-only (spec §5). Milestone 0 wires Google; Facebook/Apple come in Milestone 2. You need OAuth clients in [Google Cloud Console](https://console.cloud.google.com/) → *APIs & Services* → *Credentials* (create a project and configure the OAuth consent screen first, adding your Google account as a test user):

1. **Web application** client — this is the ID the backend validates tokens against, *and* the `webClientId` the app requests ID tokens for.
   - Put its client ID and secret in `.env` (`GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`), then restart: `docker compose up -d`.
   - Put the same client ID in `mobile/src/config.ts` as `GOOGLE_WEB_CLIENT_ID`.
2. **Android** client — package name `com.showadvisor`, plus the SHA-1 of your debug keystore:
   - Linux/macOS: `keytool -list -v -alias androiddebugkey -keystore mobile/android/app/debug.keystore -storepass android | grep SHA1`
   - Windows (PowerShell): `keytool -list -v -alias androiddebugkey -keystore mobile\android\app\debug.keystore -storepass android | Select-String SHA1`
   - No ID goes in the code — registering it in the console is enough.
3. **iOS** client (only when building on a Mac) — bundle ID `com.showadvisor`.

## 3. Run the mobile app

```sh
cd mobile
npm install
```

**Android (Linux and Windows):** start an emulator from Android Studio (Device Manager), or plug in a device with USB debugging, then:

```sh
npx react-native run-android
```

This launches the Metro bundler and installs the debug app. The app is preconfigured to reach the backend at `10.0.2.2:8000` on the Android emulator (the emulator's alias for your machine's localhost) and `localhost:8000` on the iOS simulator — see `mobile/src/config.ts`. For a **physical device**, replace the URL there with your machine's LAN IP (e.g. `http://192.168.1.20:8000`) and make sure the device is on the same network.

**iOS (macOS only):**

```sh
cd ios && bundle install && bundle exec pod install && cd ..
npx react-native run-ios
```

**Tests / typecheck:**

```sh
npm test           # jest
npx tsc --noEmit   # TypeScript
```

### Linux notes

- If `run-android` fails with `adb: not found` or "No emulators found" even though Android Studio and an AVD are installed, the SDK isn't on your shell's PATH. Add to `~/.bashrc` (then open a new terminal):

  ```sh
  export ANDROID_HOME=$HOME/Android/Sdk
  export PATH=$PATH:$ANDROID_HOME/emulator
  export PATH=$PATH:$ANDROID_HOME/platform-tools
  ```

- If the app opens with a red **"Unable to load script"** screen, Metro didn't get spawned automatically (`run-android` often can't open a new terminal window on Linux). Run it yourself and keep it open, then reload the app (press `r` in the Metro terminal):

  ```sh
  cd mobile && npm start
  ```

### Windows notes

- Run everything in PowerShell; Docker Desktop must be running before `docker compose` commands.
- If `keytool` isn't on your PATH, it lives in the JDK's `bin` folder (e.g. `C:\Program Files\Eclipse Adoptium\jdk-17...\bin`).
- Set the `ANDROID_HOME` environment variable and add `platform-tools` to PATH per the [React Native environment guide](https://reactnative.dev/docs/set-up-your-environment) if `run-android` can't find the SDK.
- Keep the project on a local NTFS path (not a network drive); long-path issues are avoided by keeping the checkout shallow, e.g. `C:\dev\ShowAdvisor`.

## 4. Verify the walking skeleton (Milestone 0.5 checkpoint)

With the backend up and the Google credentials configured:

1. `docker compose up` from a clean state brings up web + Postgres + Redis with no errors.
2. http://localhost:8000/admin/ loads.
3. Launch the app on the Android emulator (and, on a Mac, the iOS simulator).
4. Tap **Sign in with Google**, complete the flow with a test account.
5. The Profile screen shows the account's real username and email, fetched from `/api/profile/` with the JWT issued by the backend.

Per the implementation plan, **stop and confirm this manually before starting Milestone 1** — infrastructure problems are far cheaper to fix now.

## API surface (Milestone 0)

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/api/auth/google/` | POST `{"id_token": ...}` | — | Exchange a Google ID token for the app's JWT `{access, refresh}` |
| `/api/auth/token/refresh/` | POST `{"refresh": ...}` | — | Refresh an expired access token |
| `/api/profile/` | GET | Bearer JWT | `{username, email}` of the logged-in user |
| `/admin/` | — | session | Django admin |
