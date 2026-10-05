from enum import StrEnum


class LiftAxis(StrEnum):
    WORLD_UP = "world_up"
    SURFACE_NORMAL = "surface_normal"


class LibraryAssetStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
