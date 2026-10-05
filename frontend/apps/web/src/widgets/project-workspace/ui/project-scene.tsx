"use client";
import type { Project } from "@/entities/project";
import { SceneViewportContainer } from "./scene-viewport-container";
interface ProjectSceneProps {
  project: Project;
  projectId: string;
  rendererBackend: "webgl" | "webgpu";
}
export function ProjectScene(props: ProjectSceneProps) {
  return (
    <div className="relative min-h-[260px] flex-1">
      <SceneViewportContainer {...props} />
    </div>
  );
}
