# Simulator

A 3D Gaussian Splatting scene editor being developed into a robot simulation environment.
Based on [camera_path](https://github.com/vinneyto/camera_path) at commit
`06aa039306ae96b51dcdbfa6554f805dfee4c5b7` (merged CP-72).

The initial version keeps projects, the PLY library, model placement/removal with a searchable
command palette, spatial anchors, grid, profile renderer/grid settings, and both WebGPU tile and
Spark/WebGL rendering. Chat/agent, trajectories, timelines, camera playback and depth of field
are removed from the UI, API and database schema.

## Layout

- `frontend/apps/web`: Next.js/React/TypeScript app, preserving the source project's FSD structure,
  R3F/Drei/Three.js, Zustand, React Query, Tailwind/UI components, Orval and Vitest.
- `frontend/packages/gaussian-rendering`: reserved npm workspace; extracting the existing pipeline,
  passes, TSL nodes and adapters into its public API is SIM-02. Rendering currently lives in the app.
- `backend`: Python/FastAPI, async SQLAlchemy and Alembic; SQLite in development.
- `infra`: reserved for the AWS CDK deployment tasks in M1.

The frontend has one npm workspace root and one lockfile at `frontend/`. Run commands there;
installation from `apps/web` is unnecessary.

## Run locally

Requirements: Node.js 24, npm and Python 3.11+ with `uv`.

Terminal 1:

```bash
cd backend
cp .env.example .env
uv sync --all-groups
uv run alembic upgrade head
uv run uvicorn simulator.api:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:3000. Create a project to open an empty scene. Upload a PLY in Library;
use the top command palette to add/remove models or show/hide the grid. The first model is placed
at the origin; subsequent ones are placed by clicking a surface or grid. Escape cancels placement.
Hold Command on macOS or Ctrl on Windows/Linux to place anchors; drag an anchor vertically to
change its height and use its context menu to delete it.

The profile settings select WebGPU tile (default) or Spark/WebGL. WebGPU requires browser support
and a secure context (localhost qualifies); an unavailable renderer displays a message.
`NEXT_PUBLIC_API_URL` overrides the default browser API URL `http://127.0.0.1:8000`.

Development data lives at `~/.simulator/simulator.sqlite3` and `~/.simulator/library`, separate
from camera_path. Override paths with `SIMULATOR_DATABASE_URL` and `SIMULATOR_LIBRARY_DIRECTORY`.
This is a new database baseline, not an in-place migration of camera_path data.

## Checks

```bash
cd backend
uv run ruff check src tests alembic
uv run ruff format --check src tests alembic
uv run pytest
uv run openapi-export
cd ../frontend
npm run api:check
npm run typecheck
npm run lint
npm test
npm run build
```

`npm run api:generate` regenerates the client from `backend/openapi.json` and removes obsolete
schemas. `npm run format` / `format:check` use the inherited Prettier setup.
API mutations preserve project revision ETags (`If-Match`) and resource-level query invalidation.
Backend docs: http://127.0.0.1:8000/docs; health: http://127.0.0.1:8000/health.

## M1 boundaries

SIM-01 establishes the reduced application and monorepo. Full pipeline extraction, mobile layout
and real-device GPU validation, authentication, S3 and AWS deployment have their own M1 tasks.
The current API uses a shared development profile and does not yet implement authorization.
