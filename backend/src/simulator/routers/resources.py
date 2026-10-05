from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from simulator.models import (
    Anchor,
    AnchorCreate,
    AnchorUpdate,
    Project,
    ProjectCreate,
    ProjectMetadata,
    ProjectUpdate,
    ScenePoint,
    ScenePointCreate,
    ScenePointUpdate,
)
from simulator.routers.contract import ERROR_RESPONSES, MUTATION_ERROR_RESPONSES, set_revision_etag
from simulator.routers.dependencies import (
    AnchorServiceDep,
    MutationGuard,
    ProjectServiceDep,
    ScenePointServiceDep,
)

router = APIRouter()


def _with_revision(response: Response, project: Project | ProjectMetadata) -> None:
    set_revision_etag(response, project.revision)


def _deleted(project: Project) -> Response:
    return Response(
        status_code=status.HTTP_204_NO_CONTENT, headers={"ETag": f'"{project.revision}"'}
    )


def _not_found(error: KeyError) -> HTTPException:
    return HTTPException(status_code=404, detail=str(error))


@router.post(
    "/projects",
    response_model=ProjectMetadata,
    status_code=status.HTTP_201_CREATED,
    tags=["Projects"],
    summary="Create a project",
    description="Create an empty project and return only project metadata.",
    operation_id="createProject",
)
async def create_project(
    data: ProjectCreate, service: ProjectServiceDep, response: Response
) -> ProjectMetadata:
    project = await service.create_project(data)
    _with_revision(response, project)
    return await service.get_project_metadata(project.id)


@router.get(
    "/projects",
    response_model=list[ProjectMetadata],
    tags=["Projects"],
    summary="List projects",
    description="Return project metadata without nested resources.",
    operation_id="listProjects",
)
async def list_projects(service: ProjectServiceDep) -> list[ProjectMetadata]:
    return await service.list_project_metadata()


@router.get(
    "/projects/{project_id}",
    response_model=ProjectMetadata,
    tags=["Projects"],
    summary="Get project metadata",
    description="Return project metadata and its project-level revision ETag.",
    operation_id="getProject",
    responses=ERROR_RESPONSES,
)
async def get_project(
    project_id: str, service: ProjectServiceDep, response: Response
) -> ProjectMetadata:
    project = await service.get_project_metadata(project_id)
    _with_revision(response, project)
    return project


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectMetadata,
    tags=["Projects"],
    summary="Rename a project",
    description="Rename a project and return the changed metadata resource.",
    operation_id="updateProject",
    responses=MUTATION_ERROR_RESPONSES,
)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    service: ProjectServiceDep,
    response: Response,
    _guard: MutationGuard,
) -> ProjectMetadata:
    project = await service.update_project(project_id, data)
    _with_revision(response, project)
    return await service.get_project_metadata(project.id)


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Projects"],
    summary="Delete a project",
    description="Delete a project and all normalized resources.",
    operation_id="deleteProject",
    responses=MUTATION_ERROR_RESPONSES,
)
async def delete_project(
    project_id: str, service: ProjectServiceDep, _guard: MutationGuard
) -> Response:
    project = await service.get_project(project_id)
    await service.delete_project(project_id)
    return _deleted(project)


@router.post(
    "/projects/{project_id}/reset",
    response_model=ProjectMetadata,
    tags=["Projects"],
    summary="Reset a project",
    description="Clear resource state while preserving project identity and metadata.",
    operation_id="resetProject",
    responses=MUTATION_ERROR_RESPONSES,
)
async def reset_project(
    project_id: str, service: ProjectServiceDep, response: Response, _guard: MutationGuard
) -> ProjectMetadata:
    project = await service.reset_project(project_id)
    _with_revision(response, project)
    return await service.get_project_metadata(project.id)


@router.get(
    "/projects/{project_id}/anchors",
    response_model=list[Anchor],
    tags=["Anchors"],
    summary="List anchors",
    description="Return the project's spatial anchors.",
    operation_id="listAnchors",
)
async def list_anchors(
    project_id: str, service: ProjectServiceDep, response: Response
) -> list[Anchor]:
    project = await service.get_project(project_id)
    _with_revision(response, project)
    return list(project.anchors.values())


@router.post(
    "/projects/{project_id}/anchors",
    response_model=Anchor,
    status_code=status.HTTP_201_CREATED,
    tags=["Anchors"],
    summary="Create an anchor",
    description="Create an anchor and return only the changed resource.",
    operation_id="createAnchor",
    responses=MUTATION_ERROR_RESPONSES,
)
async def create_anchor(
    project_id: str,
    data: AnchorCreate,
    service: AnchorServiceDep,
    response: Response,
    _guard: MutationGuard,
) -> Anchor:
    project = await service.add_anchor(project_id, data)
    _with_revision(response, project)
    return next(reversed(project.anchors.values()))


@router.patch(
    "/projects/{project_id}/anchors/{anchor_id}",
    response_model=Anchor,
    tags=["Anchors"],
    summary="Update an anchor",
    description="Update an anchor and return only the changed resource.",
    operation_id="updateAnchor",
    responses=MUTATION_ERROR_RESPONSES,
)
async def update_anchor(
    project_id: str,
    anchor_id: str,
    data: AnchorUpdate,
    service: AnchorServiceDep,
    response: Response,
    _guard: MutationGuard,
) -> Anchor:
    try:
        project = await service.update_anchor(project_id, anchor_id, data)
    except KeyError as error:
        raise _not_found(error) from error
    _with_revision(response, project)
    return project.anchors[anchor_id]


@router.delete(
    "/projects/{project_id}/anchors/{anchor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Anchors"],
    summary="Delete an anchor",
    description="Delete an unreferenced anchor.",
    operation_id="deleteAnchor",
    responses=MUTATION_ERROR_RESPONSES,
)
async def delete_anchor(
    project_id: str, anchor_id: str, service: AnchorServiceDep, _guard: MutationGuard
) -> Response:
    try:
        project = await service.delete_anchor(project_id, anchor_id)
    except KeyError as error:
        raise _not_found(error) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return _deleted(project)


@router.get(
    "/projects/{project_id}/scene-points",
    response_model=list[ScenePoint],
    tags=["Scene points"],
    summary="List scene points",
    description="Return named world-space scene points.",
    operation_id="listScenePoints",
)
async def list_scene_points(
    project_id: str, service: ProjectServiceDep, response: Response
) -> list[ScenePoint]:
    project = await service.get_project(project_id)
    _with_revision(response, project)
    return list(project.scene_points.values())


@router.post(
    "/projects/{project_id}/scene-points",
    response_model=ScenePoint,
    status_code=status.HTTP_201_CREATED,
    tags=["Scene points"],
    summary="Create a scene point",
    description="Create a scene point and return only the changed resource.",
    operation_id="createScenePoint",
    responses=MUTATION_ERROR_RESPONSES,
)
async def create_scene_point(
    project_id: str,
    data: ScenePointCreate,
    service: ScenePointServiceDep,
    response: Response,
    _guard: MutationGuard,
) -> ScenePoint:
    project = await service.add_scene_point(project_id, data)
    _with_revision(response, project)
    return next(reversed(project.scene_points.values()))


@router.patch(
    "/projects/{project_id}/scene-points/{point_id}",
    response_model=ScenePoint,
    tags=["Scene points"],
    summary="Update a scene point",
    description="Update a scene point and return only the changed resource.",
    operation_id="updateScenePoint",
    responses=MUTATION_ERROR_RESPONSES,
)
async def update_scene_point(
    project_id: str,
    point_id: str,
    data: ScenePointUpdate,
    service: ScenePointServiceDep,
    response: Response,
    _guard: MutationGuard,
) -> ScenePoint:
    try:
        project = await service.update_scene_point(project_id, point_id, data)
    except KeyError as error:
        raise _not_found(error) from error
    _with_revision(response, project)
    return project.scene_points[point_id]


@router.delete(
    "/projects/{project_id}/scene-points/{point_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Scene points"],
    summary="Delete a scene point",
    description="Delete a named spatial scene point.",
    operation_id="deleteScenePoint",
    responses=MUTATION_ERROR_RESPONSES,
)
async def delete_scene_point(
    project_id: str,
    point_id: str,
    service: ScenePointServiceDep,
    _guard: MutationGuard,
) -> Response:
    try:
        project = await service.delete_scene_point(project_id, point_id)
    except KeyError as error:
        raise _not_found(error) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return _deleted(project)
