from simulator.models import Project, ScenePoint, ScenePointCreate, ScenePointUpdate, new_id
from simulator.repositories.scene_point import ScenePointRepository
from simulator.services.base import ServiceBase


class ScenePointService(ServiceBase):
    async def _save_points(self, draft: Project, expected: int) -> Project:
        async with self._transaction(draft, expected) as session:
            await ScenePointRepository(session).replace(draft.id, draft.scene_points)
        return draft

    async def add_scene_point(self, project_id: str, data: ScenePointCreate) -> Project:
        draft = await self.repository.get(project_id)
        expected = draft.revision
        point = ScenePoint(id=new_id(), **data.model_dump())
        draft.scene_points[point.id] = point
        return await self._save_points(draft, expected)

    async def update_scene_point(
        self, project_id: str, point_id: str, data: ScenePointUpdate
    ) -> Project:
        draft = await self.repository.get(project_id)
        expected = draft.revision
        if point_id not in draft.scene_points:
            raise KeyError(f"scene point {point_id} not found")
        patch = data.model_dump(exclude_unset=True, exclude_none=True)
        draft.scene_points[point_id] = draft.scene_points[point_id].model_copy(update=patch)
        return await self._save_points(draft, expected)

    async def delete_scene_point(self, project_id: str, point_id: str) -> Project:
        draft = await self.repository.get(project_id)
        expected = draft.revision
        if point_id not in draft.scene_points:
            raise KeyError(f"scene point {point_id} not found")
        del draft.scene_points[point_id]
        return await self._save_points(draft, expected)
