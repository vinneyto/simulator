from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    true,
)
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, composite, mapped_column

from simulator.persistence.enums import LibraryAssetStatus, LiftAxis


def enum_column(enum_type: type, constraint_name: str) -> SqlEnum:
    return SqlEnum(
        enum_type,
        values_callable=lambda values: [member.value for member in values],
        name=constraint_name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
    )


@dataclass(frozen=True)
class Vector3:
    x: float
    y: float
    z: float

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


class Base(DeclarativeBase):
    pass


class UserSettingsRecord(Base):
    __tablename__ = "user_settings"
    user_id: Mapped[str] = mapped_column(Text, primary_key=True)
    webgpu_tile_renderer: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    show_grid: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())


class ProjectRecord(Base):
    __tablename__ = "projects"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class LibraryAssetRecord(Base):
    __tablename__ = "library_assets"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    format: Mapped[str] = mapped_column(Text, nullable=False)
    object_key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[LibraryAssetStatus] = mapped_column(
        enum_column(LibraryAssetStatus, "ck_library_assets_status"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    default_rotation_x_deg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    default_rotation_y_deg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    default_rotation_z_deg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    default_scale: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    default_offset_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    default_offset_y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    default_offset_z: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class ProjectCloudRecord(Base):
    __tablename__ = "project_clouds"
    __table_args__ = (UniqueConstraint("project_id", "position", name="uq_project_cloud_position"),)
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    library_asset_id: Mapped[str] = mapped_column(
        ForeignKey("library_assets.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    visible: Mapped[bool] = mapped_column(nullable=False, default=True)
    translation_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    translation_y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    translation_z: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rotation_x_deg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rotation_y_deg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rotation_z_deg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    scale: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    offset_x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    offset_y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    offset_z: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class ProjectChildRecord:
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )


class AnchorRecord(ProjectChildRecord, Base):
    __tablename__ = "anchors"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    surface_position: Mapped[Vector3] = composite(
        mapped_column("surface_position_x", Float, nullable=False),
        mapped_column("surface_position_y", Float, nullable=False),
        mapped_column("surface_position_z", Float, nullable=False),
    )
    surface_normal: Mapped[Vector3] = composite(
        mapped_column("surface_normal_x", Float, nullable=False),
        mapped_column("surface_normal_y", Float, nullable=False),
        mapped_column("surface_normal_z", Float, nullable=False),
    )
    lift: Mapped[float] = mapped_column(Float, nullable=False)
    lift_axis: Mapped[LiftAxis] = mapped_column(
        enum_column(LiftAxis, "ck_anchors_lift_axis"), nullable=False
    )


class ScenePointRecord(ProjectChildRecord, Base):
    __tablename__ = "scene_points"
    __table_args__ = (UniqueConstraint("project_id", "id", name="uq_scene_points_project_id_id"),)
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[Vector3] = composite(
        mapped_column("position_x", Float, nullable=False),
        mapped_column("position_y", Float, nullable=False),
        mapped_column("position_z", Float, nullable=False),
    )
