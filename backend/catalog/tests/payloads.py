"""
Trimmed-but-realistic provider payload builders. The shapes mirror real
TVmaze / TMDB responses (only the fields the sync layer reads, spec §4.1),
so tests exercise the same key paths production payloads do. Every builder
takes overrides for the case under test.
"""


def tvmaze_show(tvmaze_id=250, **overrides):
    """Show-level payload: what an index page or search hit carries."""
    payload = {
        "id": tvmaze_id,
        "name": "Kirby Buckets",
        "type": "Scripted",
        "language": "English",
        "status": "Ended",
        "runtime": 30,
        "averageRuntime": 30,
        "premiered": "2014-10-20",
        "ended": "2017-02-02",
        "schedule": {"time": "07:00", "days": ["Monday"]},
        "network": {"name": "Disney XD", "country": {"code": "US"}},
        "webChannel": None,
        "externals": {"tvrage": 37394, "thetvdb": 278449, "imdb": "tt3544772"},
        "summary": "<p>The series mixes <b>live-action</b> and animation.</p>",
    }
    payload.update(overrides)
    return payload


def tvmaze_season(season_id, number):
    return {"id": season_id, "number": number, "name": "", "episodeOrder": None}


def tvmaze_episode(episode_id, season, number, name="Pilot", **overrides):
    payload = {
        "id": episode_id,
        "name": name,
        "season": season,
        "number": number,
        "type": "regular",
        "airdate": "2014-10-20",
        "airstamp": "2014-10-20T11:00:00+00:00",
        "runtime": 30,
        "summary": "<p>Kirby's drawings come to life.</p>",
    }
    payload.update(overrides)
    return payload


def tvmaze_show_full(tvmaze_id=250, seasons=None, episodes=None, **overrides):
    """Full-detail payload: what TVmazeClient.show_details returns."""
    if seasons is None:
        seasons = [tvmaze_season(9001, 1)]
    if episodes is None:
        episodes = [
            tvmaze_episode(101, 1, 1, "Pilot"),
            tvmaze_episode(102, 1, 2, "Cheer Force One"),
        ]
    return tvmaze_show(
        tvmaze_id, _embedded={"seasons": seasons, "episodes": episodes}, **overrides
    )


def tvmaze_akas():
    return [
        {"name": "Kirby et ses potes", "country": {"name": "France", "code": "FR"}},
        {"name": "Кирби Бакетс", "country": {"name": "Russia", "code": "RU"}},
    ]


def tmdb_tv(tmdb_id=61217, **overrides):
    payload = {
        "id": tmdb_id,
        "name": "Kirby Buckets",
        "overview": "13-year-old Kirby dreams of becoming a famous animator.",
        "status": "Ended",
        "first_air_date": "2014-10-20",
        "last_air_date": "2017-02-02",
        "episode_run_time": [22],
        "networks": [{"id": 44, "name": "Disney XD"}],
        "poster_path": "/kirby.jpg",
        "alternative_titles": {
            "results": [{"iso_3166_1": "FR", "title": "Kirby et ses potes"}]
        },
    }
    payload.update(overrides)
    return payload


def tmdb_movie(tmdb_id=693134, **overrides):
    """Full movie detail — `runtime` is what marks a snapshot as full."""
    payload = {
        "id": tmdb_id,
        "title": "Dune: Part Two",
        "overview": "Paul Atreides unites with Chani and the Fremen.",
        "release_date": "2024-02-27",
        "runtime": 167,
        "poster_path": "/dune2.jpg",
        "alternative_titles": {
            "titles": [{"iso_3166_1": "ES", "title": "Dune: Parte dos"}]
        },
    }
    payload.update(overrides)
    return payload


def tmdb_movie_search_hit(tmdb_id=693134, **overrides):
    """Search-result item: partial — no runtime, no alternative_titles."""
    payload = {
        "id": tmdb_id,
        "title": "Dune: Part Two",
        "overview": "Paul Atreides unites with Chani and the Fremen.",
        "release_date": "2024-02-27",
        "poster_path": "/dune2.jpg",
    }
    payload.update(overrides)
    return payload
