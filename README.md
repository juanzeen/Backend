# NBA FANtastic API 🏀

[![Python](https://img.shields.io/badge/Python-3.14+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Redis-FF4438?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![uv](https://img.shields.io/badge/uv-DE5FE9?style=for-the-badge&logo=astral&logoColor=white)](https://github.com/astral-sh/uv)
[![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

A high-performance backend catalog and analytics REST API for NBA basketball data. **NBA FANtastic API** provides structured endpoints for exploring historical legends, active NBA rosters, in-depth season metrics, team power rankings, all-time records, and upcoming game predictions.

Built with **FastAPI**, **MongoDB (PyMongo Async)**, and **Redis**, utilizing **uv** for fast Python package management and **Fly.io** for cloud deployment.

---

## Motivation & Objective

Basketball data is often scattered across multiple slow, cluttered, or overly complex platforms. The main objective of **NBA FANtastic API** is to **create a unified system where you can easily find and query the basketball data that actually matters**—from all-time historical benchmarks and career peaks to current team efficiency metrics, head-to-head player splits, and statistical game projections.

Whether for basketball enthusiasts, fantasy analysis, or powering client applications, the system curates and structures the most relevant NBA metrics into fast, predictable endpoints.

---

## Features

- **Active & Historical Players**: Browse active rosters and all-time NBA legends with career totals, averages, single-game peaks, honors, and dynamic stat sorting (`pts`, `ast`, `reb`, `stl`, `blk`).
- **Season & Game Logs**: Query season-by-season player splits, game logs, and performance against specific franchises.
- **Teams & Power Rankings**: Franchise profiles, standings, offensive/defensive ratings, pace, opponent stats, and custom-calculated power rankings/tiers.
- **Statistical Predictions**:
  - **Season Projections**: Marcel-inspired projections with age curve adjustments and confidence intervals.
  - **Matchup Predictions**: Single-game player projections factoring in opponent defensive metrics, pace, and home-court advantage.
- **All-Time Records**: Historical NBA leaderboards across major statistical categories.
- **Automated Sync Jobs**: Protected webhook endpoints triggered by GitHub Actions crons for daily stats/standings updates and weekly roster syncs.
- **Caching & Rate Limiting**: Redis cache-aside layer with dynamic TTLs and per-endpoint rate limiting.

---

## Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.14+) |
| **Data Validation** | [Pydantic v2](https://docs.pydantic.dev/) |
| **Primary Database** | [MongoDB](https://www.mongodb.com/) (Async PyMongo) |
| **Caching & Rate Limit** | [Redis](https://redis.io/) (`redis.asyncio`) |
| **Data Ingestion** | [`nba-api`](https://github.com/swar/nba_api), pandas |
| **Package Manager** | [uv](https://docs.astral.sh/uv/) by Astral |
| **Testing** | [pytest](https://docs.pytest.org/), AnyIO, HTTPX |
| **Deployment & CI/CD** | [Docker](https://www.docker.com/), [Fly.io](https://fly.io/), GitHub Actions |

---

## Quick Start

### Prerequisites
- Python 3.14+ & [uv](https://docs.astral.sh/uv/)
- [Docker & Docker Compose](https://www.docker.com/)

### 1. Setup

```bash
git clone https://github.com/juanzeen/Nba-FANtastic-API.git
cd Nba-FANtastic-API
uv sync
cp .env.example .env
```

Required `.env` variables:
```env
MONGO_URL=mongodb://nba_fantastic:superpasswordfornbafantastic@localhost:27017/nba_fantastic?authSource=admin&directConnection=true
DATABASE_NAME=nba_fantastic
REDIS_URL=redis://localhost:6379
CRON_SECRET=your_secret_token
```

### 2. Run the Application

**Option A — Full Stack in Docker:**
```bash
docker compose up -d --build
```

**Option B — Local Development (Databases in Docker):**
```bash
docker compose up -d mongodb redis
uv run python seed/populate.py          # Optional: seed initial dataset
uv run fastapi dev src/app/main.py      # Starts API at http://localhost:8000
```

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### 3. Run Tests

```bash
uv run pytest
```

---

## API Endpoints

All resource routes are prefixed with `/api/v1`.

### System & Cron Jobs
| Method | Endpoint | Description | Cache / Auth |
| :--- | :--- | :--- | :---: |
| `GET` | `/` | Health check (API, MongoDB, Redis) | — |
| `POST` | `/api/v1/jobs/daily-sync` | Trigger daily teams, players & game logs sync | 🔒 Bearer |
| `POST` | `/api/v1/jobs/weekly-sync` | Trigger weekly team roster sync | 🔒 Bearer |

### Current NBA Players & Predictions
| Method | Endpoint | Description | Cache |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/players/` | List active players (paginated & sortable by `stat`, `period`, `order`) | — |
| `GET` | `/api/v1/players/{id}` | Get active player by ID | ⚡ Redis |
| `GET` | `/api/v1/players/search/{slug}` | Get active player by slug (e.g. `lebron-james`) | ⚡ Redis |
| `GET` | `/api/v1/players/team/{team_abb}` | List active players by team abbreviation (e.g. `LAL`) | ⚡ Redis |
| `GET` | `/api/v1/players/{player_id}/seasons` | List seasons for a player (paginated) | — |
| `GET` | `/api/v1/players/{player_id}/seasons/{season_year}` | Get detailed season log (e.g. `2024-25`) | ⚡ Redis |
| `GET` | `/api/v1/players/{id}/predictions/season` | Projected season averages & confidence intervals | ⚡ Redis |
| `GET` | `/api/v1/players/{id}/predictions/matchup/{opponent_team_id}` | Single-game projection vs. opponent (`?is_home=true`) | ⚡ Redis |

### NBA Teams
| Method | Endpoint | Description | Cache |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/teams/` | List NBA teams ordered by power ranking (paginated) | — |
| `GET` | `/api/v1/teams/{id}` | Get team profile, metrics & power ranking by ID | ⚡ Redis |
| `GET` | `/api/v1/teams/search/{abb}/` | Get team by 3-letter abbreviation (e.g. `BOS`) | ⚡ Redis |

### Historical Players & Records
| Method | Endpoint | Description | Cache |
| :--- | :--- | :--- | :---: |
| `GET` | `/api/v1/historical-players/` | List historical legends (paginated & sortable) | — |
| `GET` | `/api/v1/historical-players/{id}` | Get historical player by ID | ⚡ Redis |
| `GET` | `/api/v1/historical-players/search/{slug}` | Get historical player by slug (e.g. `michael-jordan`) | ⚡ Redis |
| `GET` | `/api/v1/historical-records/` | List all-time NBA records | ⚡ Redis |
| `GET` | `/api/v1/historical-records/{category}` | Get record by category (e.g. `ALL_TIME_PTS`) | ⚡ Redis |

---

## Project Structure

```text
Nba-FANtastic-API/
├── .github/workflows/         # CI/CD (main.yaml) & scheduled sync triggers
├── Dockerfile                 # Multi-stage Docker build
├── docker-compose.yaml        # Local MongoDB & Redis services
├── fly.toml                   # Fly.io deployment configuration
├── pyproject.toml             # Project metadata & dependencies (uv)
├── seed/                      # Data scraping (extractor.py), seeding (populate.py) & CSV/JSON datasets
└── src/app/
    ├── main.py                # FastAPI app initialization & health check
    ├── dependencies.py        # Async MongoDB & Redis client dependencies
    ├── jobs/                  # Scheduled sync logic (daily_sync.py, weekly_sync.py)
    ├── routers/               # Route handlers (players, teams, historical_*, jobs)
    ├── schemas/               # Pydantic v2 models (players, teams, predictions, seasons, base)
    ├── services/              # Prediction engines (season_predictor.py, matchup_predictor.py)
    ├── utils/                 # Redis cache helper, rate limiter & stat filter mapping
    └── tests/                 # Async Pytest suite (120+ tests)
```

---

## License

Licensed under the [MIT License](LICENSE).
