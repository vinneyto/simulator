from pathlib import Path

from httpx import ASGITransport, AsyncClient
from sqlalchemy import inspect

from simulator.api import create_app
from simulator.config import Settings
from simulator.models import Project


async def test_empty_scene_and_anchors_persist_without_animation_resources(tmp_path: Path):
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'scene.sqlite3'}",
        library_directory=tmp_path / "library",
    )
    app = create_app(settings)
    repo = app.state.project_repository
    await repo.initialize()
    try:
        async with repo.engine.connect() as connection:
            tables = await connection.run_sync(lambda conn: inspect(conn).get_table_names())
        assert set(tables) == {
            "projects",
            "anchors",
            "scene_points",
            "library_assets",
            "project_clouds",
            "user_settings",
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            created = await client.post("/api/v1/projects", json={})
            assert created.status_code == 201
            project = created.json()
            assert project["name"] == "Untitled scene"
            assert project["anchor_count"] == project["cloud_count"] == 0
            url = f"/api/v1/projects/{project['id']}"
            payload = {"label": "A1", "surface_position": [1, 2, 3], "lift": 0.5}
            assert (await client.post(f"{url}/anchors", json=payload)).status_code == 428
            added = await client.post(f"{url}/anchors", json=payload, headers={"If-Match": '"0"'})
            assert added.status_code == 201
            anchor_id = added.json()["id"]
            assert (await client.get(url)).json()["anchor_count"] == 1
            stale = await client.delete(f"{url}/anchors/{anchor_id}", headers={"If-Match": '"0"'})
            assert stale.status_code == 409
            invalid = await client.patch(
                f"{url}/anchors/{anchor_id}",
                json={"surface_normal": [0, 0, 0]},
                headers={"If-Match": '"1"'},
            )
            assert invalid.status_code == 422
    finally:
        await repo.close()
    # Re-open a fresh app/repository, not just an in-memory snapshot.
    reopened = create_app(settings)
    await reopened.state.project_repository.initialize()
    try:
        async with AsyncClient(
            transport=ASGITransport(app=reopened), base_url="http://test"
        ) as client:
            anchors = (await client.get(f"{url}/anchors")).json()
            assert anchors[0]["id"] == anchor_id
            assert anchors[0]["surface_position"] == [1, 2, 3]
            reset = await client.post(f"{url}/reset", headers={"If-Match": '"1"'})
            assert reset.status_code == 200
            assert reset.json()["anchor_count"] == 0
            assert (await client.get(f"{url}/anchors")).json() == []
            assert (await client.delete(url, headers={"If-Match": '"2"'})).status_code == 204
            assert (await client.get(url)).status_code == 404
    finally:
        await reopened.state.project_repository.close()


def test_contract_has_only_scene_resources():
    schema = create_app().openapi()
    paths = schema["paths"]
    assert "/api/v1/projects" in paths
    assert "/api/v1/library" in paths
    assert "/api/v1/profile/settings" in paths
    serialized = str(schema).lower()
    for excluded in ["trajectory", "keyframe", "timeline", "depth-of-field", "chat", "openai"]:
        assert excluded not in serialized
    assert set(Project.model_fields) == {"id", "name", "revision", "anchors", "scene_points"}


async def test_named_points_can_be_deleted_without_camera_references(tmp_path):
    app = create_app(
        Settings(
            _env_file=None,
            database_url=f"sqlite+aiosqlite:///{tmp_path / 'points.sqlite3'}",
            library_directory=tmp_path / "files",
        )
    )
    await app.state.project_repository.initialize()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            scene = (await client.post("/api/v1/projects", json={})).json()
            url = f"/api/v1/projects/{scene['id']}/scene-points"
            created = await client.post(
                url, json={"label": "Point", "position": [0, 1, 2]}, headers={"If-Match": '"0"'}
            )
            assert created.status_code == 201
            deleted = await client.delete(
                f"{url}/{created.json()['id']}", headers={"If-Match": '"1"'}
            )
            assert deleted.status_code == 204
            assert (await client.get(url)).json() == []
    finally:
        await app.state.project_repository.close()
