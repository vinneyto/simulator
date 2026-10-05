from __future__ import annotations

from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

Vec3 = tuple[float, float, float]


def new_id() -> str:
    return str(uuid4())


class AnchorCreate(BaseModel):
    label: str = Field(min_length=1, max_length=64)
    surface_position: Vec3
    surface_normal: Vec3 = (0.0, 1.0, 0.0)
    lift: float = 0.0
    lift_axis: Literal["world_up", "surface_normal"] = "world_up"

    @field_validator("surface_normal")
    @classmethod
    def normal_must_be_nonzero(cls, value: Vec3) -> Vec3:
        if sum(component * component for component in value) < 1e-16:
            raise ValueError("surface_normal must be non-zero")
        return value


class Anchor(AnchorCreate):
    id: str = Field(default_factory=new_id)


class AnchorUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=64)
    surface_position: Vec3 | None = None
    surface_normal: Vec3 | None = None
    lift: float | None = None
    lift_axis: Literal["world_up", "surface_normal"] | None = None

    @field_validator("surface_normal")
    @classmethod
    def normal_must_be_nonzero(cls, value: Vec3 | None) -> Vec3 | None:
        if value is not None and sum(component * component for component in value) < 1e-16:
            raise ValueError("surface_normal must be non-zero")
        return value


class ScenePointCreate(BaseModel):
    label: str = Field(min_length=1, max_length=64)
    position: Vec3


class ScenePoint(ScenePointCreate):
    id: str = Field(default_factory=new_id)


class ScenePointUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=64)
    position: Vec3 | None = None


class Project(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str = Field(default="Untitled scene", min_length=1, max_length=128)
    revision: int = 0
    anchors: dict[str, Anchor] = Field(default_factory=dict)
    scene_points: dict[str, ScenePoint] = Field(default_factory=dict)


class ProjectCreate(BaseModel):
    name: str = Field(default="Untitled scene", min_length=1, max_length=128)


class ProjectUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=128)


class ProjectMetadata(BaseModel):
    id: str
    name: str
    revision: int
    anchor_count: int
    cloud_count: int


class FieldError(BaseModel):
    location: list[str | int]
    message: str
    type: str


class ErrorResponse(BaseModel):
    code: str
    detail: str
    field_errors: list[FieldError] | None = None
