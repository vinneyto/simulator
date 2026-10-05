import type { QueryClient } from "@tanstack/react-query";
import { projectKeys } from "./project-queries";
type Resource = "anchors" | "scenePoints" | "all";
export async function invalidateProjectResource(
  queryClient: QueryClient,
  projectId: string,
  resource: Resource,
) {
  const keys = [
    projectKeys.detail(projectId),
    projectKeys.list(),
    ...(resource === "all"
      ? [projectKeys.anchors(projectId), projectKeys.scenePoints(projectId)]
      : [projectKeys[resource](projectId)]),
  ];
  await Promise.all(
    keys.map((queryKey) => queryClient.invalidateQueries({ queryKey })),
  );
}
