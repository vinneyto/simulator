from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from simulator.models import Project
from simulator.repositories import ProjectRepository
from simulator.services.revisions import advance_project_revision


class ServiceBase:
    def __init__(self, repository: ProjectRepository) -> None:
        self.repository = repository

    @asynccontextmanager
    async def _transaction(self, draft: Project, expected: int) -> AsyncIterator[AsyncSession]:
        async with self.repository.session_factory.begin() as session:
            await advance_project_revision(session, draft.id, expected)
            yield session
        draft.revision = expected + 1
