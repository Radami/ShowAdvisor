# ShowAdvisor

A self-owned movie & TV series tracker (a TV Time replacement): track what
you've watched, subscribe to shows and movies, and get notified about upcoming
episodes and releases. A Django + PostgreSQL backend and a React Native app
(Android + iOS from one codebase).

> **Contributors:** architecture, build status, one-time credential setup
> (Google Sign-In, TMDB), and the API reference live in
> [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Prerequisites

| Tool | Linux | Windows | macOS |
|---|---|---|---|
| Docker + Compose | [Docker Engine](https://docs.docker.com/engine/install/) or Docker Desktop | [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) with the WSL 2 backend | [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/) |
| Node.js ≥ 20 + npm | via [nvm](https://github.com/nvm-sh/nvm) or distro packages | via [nvm-windows](https://github.com/coreybutler/nvm-windows) or the installer | via [nvm](https://github.com/nvm-sh/nvm) or Homebrew |
| JDK 17–20 | distro packages (e.g. `openjdk-17-jdk`) | [Temurin 17](https://adoptium.net/) | [Temurin 17](https://adoptium.net/) or Homebrew |
| Android Studio + SDK + an emulator (AVD) | [reactnative.dev environment setup](https://reactnative.dev/docs/set-up-your-environment) | same guide, Windows tab | same guide, macOS tab |
| Xcode (iOS builds only) | — not possible on Linux | — not possible on Windows | required for iOS |

> The same JS codebase runs on Android and iOS. iOS can only be built on macOS;
> on Linux and Windows, develop against the Android emulator.

## Run the backend

Works identically on Linux, macOS, and Windows (PowerShell or CMD, with Docker
Desktop running).

```sh
# from the repo root
cp .env.example .env        # Windows CMD: copy .env.example .env
docker compose up --build
```

That starts three containers: Django (`web`, http://localhost:8000), PostgreSQL,
and Redis. Migrations run automatically on startup, and `backend/` is
bind-mounted with auto-reload, so edits apply without rebuilding.

Verify it's up:

- http://localhost:8000/admin/ shows the Django admin login page.
- `curl http://localhost:8000/api/profile/` returns HTTP 401 with
  `{"detail":"Authentication credentials were not provided."}` (proves DRF + JWT
  auth is wired).

Common commands:

```sh
docker compose up -d          # run in the background
docker compose logs -f web    # follow Django logs
docker compose down           # stop everything (data survives in a named volume)
docker compose down -v        # stop AND wipe the database
```

> To actually sign in you need Google OAuth credentials, and movie data needs a
> TMDB key. Both are one-time setup — see
> [Configuration in `ARCHITECTURE.md`](ARCHITECTURE.md#configuration).

## Run the mobile app

```sh
cd mobile
npm install
```

### Android (Linux, Windows, macOS)

Start an emulator from Android Studio (Device Manager), or plug in a device with
USB debugging, then:

```sh
npx react-native run-android
```

This launches the Metro bundler and installs the debug app. It's preconfigured to
reach the backend at `10.0.2.2:8000` on the Android emulator (the emulator's alias
for your machine's localhost) and `localhost:8000` on the iOS simulator — see
`mobile/src/config.ts`. For a **physical device**, replace the URL there with your
machine's LAN IP (e.g. `http://192.168.1.20:8000`) and put the device on the same
network.

### iOS (macOS only)

```sh
cd ios && bundle install && bundle exec pod install && cd ..
npx react-native run-ios
```

### Linux notes

- If `run-android` fails with `adb: not found` or "No emulators found" even though
  Android Studio and an AVD are installed, the SDK isn't on your shell's PATH. Add
  to `~/.bashrc` (then open a new terminal):

  ```sh
  export ANDROID_HOME=$HOME/Android/Sdk
  export PATH=$PATH:$ANDROID_HOME/emulator
  export PATH=$PATH:$ANDROID_HOME/platform-tools
  ```

- If the app opens with a red **"Unable to load script"** screen, Metro didn't get
  spawned automatically (`run-android` often can't open a new terminal window on
  Linux). Run it yourself and keep it open, then reload the app (press `r` in the
  Metro terminal):

  ```sh
  cd mobile && npm start
  ```

### Windows notes

- Run everything in PowerShell; Docker Desktop must be running before
  `docker compose` commands.
- If `keytool` isn't on your PATH, it lives in the JDK's `bin` folder (e.g.
  `C:\Program Files\Eclipse Adoptium\jdk-17...\bin`).
- Set the `ANDROID_HOME` environment variable and add `platform-tools` to PATH per
  the [React Native environment guide](https://reactnative.dev/docs/set-up-your-environment)
  if `run-android` can't find the SDK.
- Keep the project on a local NTFS path (not a network drive), e.g.
  `C:\dev\ShowAdvisor`, to avoid long-path issues.

## Tests & coverage

### Backend (Django + pytest)

Runs inside the `web` container (the dev image includes the test dependencies).
Start the stack first (`docker compose up -d`), then:

```sh
docker compose exec web pytest                              # run the test suite
docker compose exec web pytest --cov=. --cov-report=term-missing   # with coverage
```

### Mobile (Jest + React Native Testing Library)

```sh
cd mobile
npm test                # run the test suite
npm run test:coverage   # with a coverage report
npm run test:watch      # watch mode
npx tsc --noEmit        # TypeScript typecheck
```
