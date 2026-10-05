"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { projectApi, projectKeys } from "@/entities/project";
import { invalidateProjectResource } from "@/entities/project/api/invalidate-project-resource";
import { forgetProjectRevision } from "@/shared/api/orval-fetch";

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: projectApi.delete,
    onSuccess: async (_, projectId) => {
      forgetProjectRevision(projectId);
      await queryClient.invalidateQueries({ queryKey: projectKeys.list() });
      queryClient.removeQueries({ queryKey: projectKeys.detail(projectId) });
    },
  });
}

export function useDeleteAnchor(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => projectApi.deleteAnchor(projectId, id),
    onSuccess: () =>
      invalidateProjectResource(queryClient, projectId, "anchors"),
    onError: () => invalidateProjectResource(queryClient, projectId, "anchors"),
  });
}
