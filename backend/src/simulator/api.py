from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from scalar_fastapi import get_scalar_api_reference
from starlette.exceptions import HTTPException as StarletteHTTPException

from simulator.config import Settings, settings
from simulator.dev.library_storage import LocalLibraryStorage
from simulator.repositories import ProjectNotFoundError, ProjectRepository, RevisionConflictError
from simulator.repositories.library import LibraryRepository
from simulator.repositories.project_cloud import ProjectCloudRepository
from simulator.repositories.user_settings import UserSettingsRepository
from simulator.routers.dependencies import PreconditionRequiredError
from simulator.routers.library import router as library_router
from simulator.routers.profile import router as profile_router
from simulator.routers.project_clouds import router as project_cloud_router
from simulator.routers.resources import router as resource_router
from simulator.services import AnchorService, ProjectService, ScenePointService
from simulator.services.library import LibraryService
from simulator.services.library_storage import LibraryStorage
from simulator.services.project_clouds import ProjectCloudService
from simulator.services.user_settings import UserSettingsService

API_PREFIX = "/api/v1"
OPENAPI_URL = f"{API_PREFIX}/openapi.json"
ETAG_OPERATION_IDS = {
    "createProject",
    "getProject",
    "listAnchors",
    "updateProject",
    "resetProject",
    "createAnchor",
    "updateAnchor",
    "deleteAnchor",
    "listScenePoints",
    "createScenePoint",
    "updateScenePoint",
    "deleteScenePoint",
    "listProjectClouds",
    "createProjectCloud",
    "updateProjectCloud",
    "deleteProjectCloud",
}


def _is_versioned(request: Request) -> bool:
    return request.url.path.startswith(f"{API_PREFIX}/")


def _error_content(
    request: Request, code: str, detail: str, field_errors: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    if not _is_versioned(request):
        if field_errors is not None:
            return {"detail": field_errors}
        return {"detail": detail}
    content: dict[str, Any] = {"code": code, "detail": detail}
    if field_errors is not None:
        content["field_errors"] = field_errors
    return content


def create_app(
    app_settings: Settings | None = None,
    repository: ProjectRepository | None = None,
    library_storage: LibraryStorage | None = None,
) -> FastAPI:
    configured = app_settings or settings
    owns_repository = repository is None
    project_repository = repository or ProjectRepository(configured.database_url)
    storage = library_storage or LocalLibraryStorage(configured.library_directory)
    library_service = LibraryService(LibraryRepository(project_repository.session_factory), storage)
    project_cloud_service = ProjectCloudService(
        ProjectCloudRepository(project_repository.session_factory),
        library_service.repository,
        storage,
    )
    project_service = ProjectService(project_repository)
    anchor_service = AnchorService(project_repository)
    scene_point_service = ScenePointService(project_repository)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize = getattr(project_repository, "initialize", None)
        if initialize is not None:
            await initialize()
        yield
        if owns_repository:
            await project_repository.close()

    application = FastAPI(
        title="Simulator API",
        summary="3DGS robot simulator scene API",
        description="Manage scenes, 3DGS library assets, cloud instances and spatial anchors.",
        version="1.0.0",
        lifespan=lifespan,
        openapi_url=OPENAPI_URL,
        docs_url=None,
        redoc_url=None,
        openapi_tags=[
            {"name": "Projects", "description": "Project lifecycle and metadata."},
            {"name": "Anchors", "description": "Lifted spatial anchors."},
            {"name": "Scene points", "description": "Named world-space reference points."},
            {"name": "Library", "description": "Uploaded 3DGS assets, independent of projects."},
            {"name": "Clouds", "description": "Library cloud instances in projects."},
            {"name": "Profile", "description": "Settings of the current user."},
        ],
    )
    application.state.project_service = project_service
    application.state.library_service = library_service
    application.state.project_cloud_service = project_cloud_service
    application.state.project_repository = project_repository
    application.state.dev_user_id = configured.dev_user_id
    application.state.user_settings_service = UserSettingsService(
        UserSettingsRepository(project_repository.session_factory)
    )
    application.state.anchor_service = anchor_service
    application.state.scene_point_service = scene_point_service
    application.state.project_mutation_locks: dict[str, asyncio.Lock] = {}
    application.add_middleware(
        CORSMiddleware,
        allow_origins=configured.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["ETag"],
    )

    @application.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/docs", include_in_schema=False)
    async def scalar_docs():
        return get_scalar_api_reference(
            openapi_url=application.openapi_url or OPENAPI_URL,
            title=f"{application.title} — Scalar",
        )

    @application.exception_handler(ProjectNotFoundError)
    async def project_not_found(request: Request, error: ProjectNotFoundError) -> JSONResponse:
        detail = f"project {error.args[0]} not found"
        return JSONResponse(
            status_code=404, content=_error_content(request, "project_not_found", detail)
        )

    @application.exception_handler(RevisionConflictError)
    async def revision_conflict(request: Request, error: RevisionConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=409, content=_error_content(request, "revision_conflict", str(error))
        )

    @application.exception_handler(PreconditionRequiredError)
    async def precondition_required(
        request: Request, error: PreconditionRequiredError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=428, content=_error_content(request, "if_match_required", str(error))
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        if not _is_versioned(request):
            return JSONResponse(
                status_code=422, content={"detail": jsonable_encoder(error.errors())}
            )
        fields = [
            {"location": list(item["loc"]), "message": item["msg"], "type": item["type"]}
            for item in error.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_error_content(
                request, "validation_error", "Request validation failed", fields
            ),
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
        codes = {404: "not_found", 409: "reference_conflict", 502: "upstream_error"}
        return JSONResponse(
            status_code=error.status_code,
            content=_error_content(
                request, codes.get(error.status_code, "http_error"), str(error.detail)
            ),
            headers=error.headers,
        )

    application.include_router(resource_router, prefix=API_PREFIX)
    application.include_router(library_router, prefix=API_PREFIX)
    application.include_router(project_cloud_router, prefix=API_PREFIX)
    application.include_router(profile_router, prefix=API_PREFIX)
    if isinstance(storage, LocalLibraryStorage):
        from simulator.dev.library_routes import router as local_library_router

        application.include_router(local_library_router, prefix=API_PREFIX)

    def versioned_openapi() -> dict[str, Any]:
        if application.openapi_schema is not None:
            return application.openapi_schema
        schema = get_openapi(
            title=application.title,
            version=application.version,
            summary=application.summary,
            description=application.description,
            routes=application.routes,
            tags=application.openapi_tags,
        )
        for path, path_item in schema["paths"].items():
            if not path.startswith(f"{API_PREFIX}/"):
                continue
            for method, operation in path_item.items():
                if method not in {"post", "patch", "delete"} or "{project_id}" not in path:
                    continue
                for parameter in operation.get("parameters", []):
                    if parameter["in"] == "header" and parameter["name"] == "If-Match":
                        parameter["required"] = True
                        parameter["schema"] = {"type": "string", "examples": ['"4"']}
            for operation in path_item.values():
                if (
                    not isinstance(operation, dict)
                    or operation.get("operationId") not in ETAG_OPERATION_IDS
                ):
                    continue
                for response in operation.get("responses", {}).values():
                    if "content" in response and any(
                        media_type == "application/json" for media_type in response["content"]
                    ):
                        response.setdefault("headers", {})["ETag"] = {
                            "description": "Revision of the returned project snapshot.",
                            "schema": {"type": "string", "examples": ['"4"']},
                        }
                        break
        application.openapi_schema = schema
        return schema

    application.openapi = versioned_openapi
    return application


app = create_app()
