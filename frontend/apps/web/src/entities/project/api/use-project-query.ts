"use client";

import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  useGetProject,
  useListAnchors,
  useListScenePoints,
} from "@/shared/api/generated/client";
import { rememberProjectRevision } from "@/shared/api/orval-fetch";
import type { Project } from "../model/types";
import { projectKeys } from "./project-keys";

export function useProjectQuery(projectId: string) {
  const queryClient = useQueryClient();
  const metadata = useGetProject(projectId);
  const anchors = useListAnchors(projectId);
  const points = useListScenePoints(projectId);
  const queries = [metadata, anchors, points];
  const revisionSignature = queries
    .map((query) => query.data?.headers.get("ETag") ?? "")
    .join(":");
  useEffect(() => {
    const revisions = revisionSignature
      .split(":")
      .map((etag) => (etag ? Number(etag.replaceAll('"', "")) : NaN));
    const latest = Math.max(...revisions.filter(Number.isFinite));
    if (!Number.isFinite(latest)) return;
    rememberProjectRevision(projectId, latest);
    const keys = [
      projectKeys.detail(projectId),
      projectKeys.anchors(projectId),
      projectKeys.scenePoints(projectId),
    ];
    revisions.forEach((revision, index) => {
      if (Number.isFinite(revision) && revision < latest) {
        void queryClient.invalidateQueries({ queryKey: keys[index] });
      }
    });
  }, [revisionSignature, projectId, queryClient]);
  const pending = queries.some((query) => query.isPending);
  const error = queries.find((query) => query.error)?.error ?? null;
  const data =
    !pending && !error
      ? (() => {
          const project = metadata.data!.data as {
            id: string;
            name: string;
            revision: number;
          };
          rememberProjectRevision(projectId, project.revision);
          // Pydantic serializes defaults and ids on every read. The Project shape here is
          // an editor view composed from generated resource responses, never an API payload.
          const byId = (items: Array<{ id?: string }>) =>
            Object.fromEntries(items.map((item) => [item.id!, item]));
          return {
            ...project,
            anchors: byId(anchors.data!.data as Array<{ id?: string }>),
            scene_points: byId(points.data!.data as Array<{ id?: string }>),
          } as Project;
        })()
      : undefined;
  return { data, isPending: pending, error };
}
