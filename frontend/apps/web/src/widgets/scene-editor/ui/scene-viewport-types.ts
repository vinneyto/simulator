import type { ReactNode } from "react";

import type { Anchor, Vec3 } from "@/entities/project";
import type { ProjectCloud } from "@/shared/api/generated/model";
import type { SceneSurfaceBackground } from "@/shared/scene-surface";
import type { ContextMenuPosition } from "@/shared/ui";

export interface SceneViewportProps {
  anchors: Anchor[];
  clouds: ProjectCloud[];
  initialCloudIds: string[] | null;
  onAddAnchor: (position: Vec3, normal: Vec3) => void;
  onAddCloud: (assetId: string, position: Vec3) => Promise<boolean>;
  onDeleteAnchor: (anchor: Anchor) => void;
  onUpdateAnchorLift: (anchorId: string, lift: number) => Promise<void>;
}

export interface SceneViewportRenderContext {
  background: SceneSurfaceBackground;
  dark: boolean;
  onOpenAnchorMenu: (anchor: Anchor, position: ContextMenuPosition) => void;
  onSurfaceError: (cloudId: string, error: Error) => void;
  onSurfaceLoading: (cloudId: string) => void;
  onSurfaceReady: (cloudId: string) => void;
}

export interface SceneViewportFrameProps {
  available: boolean | null | undefined;
  onDeleteAnchor: (anchor: Anchor) => void;
  clouds: ProjectCloud[];
  unavailableMessage?: string;
  renderScene: (context: SceneViewportRenderContext) => ReactNode;
}
