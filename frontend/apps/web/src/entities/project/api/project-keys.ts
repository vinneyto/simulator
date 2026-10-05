import {
  getGetProjectQueryKey,
  getListAnchorsQueryKey,
  getListProjectsQueryKey,
  getListScenePointsQueryKey,
} from "@/shared/api/generated/client";
export const projectKeys = {
  all: ["/api/v1/projects"] as const,
  list: getListProjectsQueryKey,
  detail: getGetProjectQueryKey,
  anchors: getListAnchorsQueryKey,
  scenePoints: getListScenePointsQueryKey,
};
