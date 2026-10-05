"use client";
import { LoaderCircle } from "lucide-react";
import { useProjectQuery } from "@/entities/project";
import { useUserSettings } from "@/features/user-settings";
import { ProjectHeader } from "./project-header";
import { ProjectScene } from "./project-scene";
interface ProjectWorkspaceProps {
  projectId: string;
}
export function ProjectWorkspace({ projectId }: ProjectWorkspaceProps) {
  const { webGpuTileRenderer, loading: settingsLoading } = useUserSettings();
  const query = useProjectQuery(projectId);
  if (query.isPending || settingsLoading)
    return (
      <main className="flex h-screen items-center justify-center">
        <LoaderCircle className="size-5 animate-spin text-muted-foreground" />
      </main>
    );
  if (!query.data)
    return (
      <main className="flex h-screen items-center justify-center p-6 text-xs text-destructive">
        {query.error instanceof Error
          ? query.error.message
          : "Project not found"}
      </main>
    );
  return (
    <main className="flex h-screen min-h-0 flex-col overflow-hidden">
      <ProjectHeader project={query.data} projectId={projectId} />
      <ProjectScene
        project={query.data}
        projectId={projectId}
        rendererBackend={webGpuTileRenderer ? "webgpu" : "webgl"}
      />
    </main>
  );
}
