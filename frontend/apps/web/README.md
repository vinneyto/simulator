# Simulator web app

The app is the `@simulator/web` npm workspace. Install dependencies and run `dev`, `build`,
`typecheck`, `lint`, `test`, `api:generate` and `api:check` from `frontend/`.

FSD structure: `app` composes routes, `widgets` compose scenes/pages, `features` own user actions,
`entities` own project query composition and spatial data, `shared` owns reusable UI/API/rendering.
React Query owns backend metadata, anchors, points, library, model instances and user settings;
Zustand owns active tools, hover and pending placement. The two rendering adapters implement
SceneSurface. The existing pipeline and adapters will move to the dedicated workspace in SIM-02.

See the repository README for startup, environment variables and scope.
