from sqlalchemy import delete

from simulator.models import Project, ProjectCreate, ProjectMetadata, ProjectUpdate, new_id
from simulator.persistence.models import ProjectCloudRecord, ProjectRecord
from simulator.repositories.anchor import AnchorRepository
from simulator.repositories.scene_point import ScenePointRepository
from simulator.services.base import ServiceBase


class ProjectService(ServiceBase):
    async def create_project(self, data: ProjectCreate) -> Project:
        project = Project(id=new_id(), name=data.name)
        await self.repository.initialize()
        async with self.repository.session_factory.begin() as session:
            session.add(ProjectRecord(id=project.id, name=project.name, revision=0))
            await session.flush()
        return project

    async def list_projects(self) -> list[Project]:
        return await self.repository.list()

    async def list_project_metadata(self) -> list[ProjectMetadata]:
        return await self.repository.list_metadata()

    async def get_project_metadata(self, project_id: str) -> ProjectMetadata:
        return await self.repository.get_metadata(project_id)

    async def get_project(self, project_id: str) -> Project:
        return await self.repository.get(project_id)

    async def update_project(self, project_id: str, data: ProjectUpdate) -> Project:
        draft = await self.repository.get(project_id)
        expected = draft.revision
        draft.name = data.name
        async with self._transaction(draft, expected) as session:
            record = await session.get(ProjectRecord, project_id)
            record.name = draft.name
        return draft

    async def delete_project(self, project_id: str) -> None:
        await self.repository.delete(project_id)

    async def reset_project(self, project_id: str) -> Project:
        current = await self.repository.get(project_id)
        draft = Project(id=current.id, name=current.name, revision=current.revision)
        async with self._transaction(draft, current.revision) as session:
            await session.execute(
                delete(ProjectCloudRecord).where(ProjectCloudRecord.project_id == project_id)
            )
            await AnchorRepository(session).replace(project_id, {})
            await ScenePointRepository(session).replace(project_id, {})
        return draft
