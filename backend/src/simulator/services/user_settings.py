from pydantic import BaseModel, ConfigDict, StrictBool
from sqlalchemy.exc import IntegrityError

from simulator.repositories.user_settings import UserSettingsRepository


class UserSettings(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    webgpu_tile_renderer: bool
    show_grid: bool


class UserSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    webgpu_tile_renderer: StrictBool = True
    show_grid: StrictBool = True


class UserSettingsService:
    def __init__(self, repository: UserSettingsRepository) -> None:
        self.repository = repository

    async def get(self, user_id: str) -> UserSettings:
        record = await self.repository.get(user_id)
        return (
            UserSettings.model_validate(record)
            if record is not None
            else UserSettings(webgpu_tile_renderer=True, show_grid=True)
        )

    async def update(self, user_id: str, data: UserSettingsUpdate) -> UserSettings:
        changes = data.model_dump(exclude_unset=True)
        try:
            async with self.repository.sessions.begin() as session:
                record = await self.repository.update(session, user_id, changes)
        except IntegrityError:
            async with self.repository.sessions.begin() as session:
                record = await self.repository.update(session, user_id, changes)
        return UserSettings.model_validate(record)
