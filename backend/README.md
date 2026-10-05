# Simulator backend

FastAPI with async SQLAlchemy repositories/services, Pydantic resource models and Alembic.
The six scene tables store projects, anchors, named scene points, library assets, project cloud
instances and user settings. There are no animation, trajectory or chat tables.

Development uses SQLite in `~/.simulator/simulator.sqlite3` and local PLY files under
`~/.simulator/library`. Configuration uses `SIMULATOR_` environment variables; `.env.example`
documents overrides. The initial migration `0001` belongs to this project, not camera_path.

Run `uv sync --all-groups`, `uv run alembic upgrade head`, then
`uv run uvicorn simulator.api:app --reload`. Canonical endpoints live at `/api/v1`; mutating a
project resource requires its current revision in `If-Match`. Resource responses carry ETags.

`uv run openapi-export` writes `openapi.json`; run frontend `api:generate` after changing contracts.
`uv run pytest` tests persistence, concurrency, library/cloud and profile behavior.
The API currently uses a shared development profile. Authorization and production storage belong
to subsequent M1 tasks. See the root README for all checks and the browser frontend setup.
