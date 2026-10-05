import { OrbitControls } from "@react-three/drei";
import { useThree } from "@react-three/fiber";
import { useEffect, useRef, useState } from "react";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";

import type { Anchor, Vec3 } from "@/entities/project";
import type { ProjectCloud } from "@/shared/api/generated/model";
import { getAnchorLabel } from "@/features/anchor-creation";
import { useGaussianRenderingSettingsStore } from "@/features/gaussian-rendering-settings";
import {
  useActiveEditorTool,
  useCloudPlacement,
  useEditorHoverCursor,
  useSceneGrid,
} from "@/features/project-editor";
import {
  SceneSurfaceProvider,
  type SceneSurfaceReady,
  type SceneSurfaceBackground,
  useGaussianRenderingBackend,
} from "@/shared/scene-surface";
import type { ContextMenuPosition } from "@/shared/ui";

import { AnchorMarker } from "./anchor-marker";
import { AnchorHeightEditingOverlay } from "./anchor-height-editing-overlay";
import { AnchorPlacementPreview } from "./anchor-placement-preview";
import { CloudPlacementPreview } from "./cloud-placement-preview";
import { frameSurface } from "./frame-surface";
import { isGaussianSurfacePickActive } from "../lib/is-gaussian-surface-pick-active";
import { resolveInitialSceneBounds } from "./resolve-initial-scene-bounds";
import { ProjectCloudSurface } from "./project-cloud-surface";
import { SceneGrid } from "./scene-grid";
import { useAnchorPlacement } from "./use-anchor-placement";
import { useCloudPlacementInteraction } from "./use-cloud-placement-interaction";
import { useAnchorHeightEditing } from "./use-anchor-height-editing";
import { useStopOrbitControlsInertia } from "./use-stop-orbit-controls-inertia";

interface SceneContentsProps {
  anchors: Anchor[];
  clouds: ProjectCloud[];
  initialCloudIds: string[] | null;
  background: SceneSurfaceBackground;
  dark: boolean;
  onAddAnchor: (position: Vec3, normal: Vec3) => void;
  onAddCloud: (assetId: string, position: Vec3) => Promise<boolean>;
  onSurfaceError: (cloudId: string, error: Error) => void;
  onSurfaceLoading: (cloudId: string) => void;
  onSurfaceReady: (cloudId: string) => void;
  onUpdateAnchorLift: (anchorId: string, lift: number) => Promise<void>;
  onOpenAnchorMenu: (anchor: Anchor, position: ContextMenuPosition) => void;
}

export function SceneContents({
  anchors,
  clouds,
  initialCloudIds,
  background,
  dark,
  onAddAnchor,
  onAddCloud,
  onSurfaceError,
  onSurfaceLoading,
  onSurfaceReady,
  onUpdateAnchorLift,
  onOpenAnchorMenu,
}: SceneContentsProps) {
  const camera = useThree((state) => state.camera);
  const activeTool = useActiveEditorTool();
  const { showGrid } = useSceneGrid();
  useEditorHoverCursor();
  const gaussianDprMode = useGaussianRenderingSettingsStore(
    (state) => state.dprMode,
  );
  const renderingBackend = useGaussianRenderingBackend(
    background,
    gaussianDprMode,
  );
  const placement = useAnchorPlacement({ onPlace: onAddAnchor });
  const cloudPlacement = useCloudPlacementInteraction({
    onPlace: onAddCloud,
    clouds,
  });
  const { pendingCloud } = useCloudPlacement();
  const heightEditing = useAnchorHeightEditing({
    anchors,
    onCommit: onUpdateAnchorLift,
  });
  const orbitControlsRef = useRef<OrbitControlsImpl>(null);
  const framedInitialScene = useRef(false);
  const cloudBounds = useRef(new Map<string, SceneSurfaceReady["bounds"]>());
  const cloudErrors = useRef(new Set<string>());
  const [orbitTarget, setOrbitTarget] = useState<Vec3>([0, 0, 0]);
  useStopOrbitControlsInertia(orbitControlsRef, activeTool !== null);

  useEffect(() => {
    renderingBackend.invalidate();
  }, [anchors, renderingBackend]);

  function fitClouds(cloudIds: readonly string[]): boolean {
    const currentIds = new Set(clouds.map((cloud) => cloud.id));
    const bounds = resolveInitialSceneBounds(
      cloudIds,
      currentIds,
      cloudBounds.current,
      cloudErrors.current,
    );
    if (bounds === undefined || bounds === null) return false;
    frameSurface(camera, bounds, setOrbitTarget);
    return true;
  }

  function tryFrameInitialScene() {
    if (framedInitialScene.current || !initialCloudIds?.length) return;
    if (fitClouds(initialCloudIds)) framedInitialScene.current = true;
  }

  function handleSurfaceReady(cloudId: string, surface: SceneSurfaceReady) {
    cloudPlacement.finishPlacement(cloudId);
    cloudBounds.current.set(cloudId, surface.bounds);
    cloudErrors.current.delete(cloudId);
    tryFrameInitialScene();
    onSurfaceReady(cloudId);
  }

  function handleSurfaceError(cloudId: string, error: Error) {
    cloudBounds.current.delete(cloudId);
    cloudErrors.current.add(cloudId);
    tryFrameInitialScene();
    onSurfaceError(cloudId, error);
  }

  function handleSurfaceLoading(cloudId: string) {
    cloudBounds.current.delete(cloudId);
    cloudErrors.current.delete(cloudId);
    onSurfaceLoading(cloudId);
  }

  function handleOrbitEnd() {
    const controls = orbitControlsRef.current;
    if (controls !== null) setOrbitTarget(controls.target.toArray() as Vec3);
  }
  const editorVisible = true;
  // Equal projected depths share a z-index, so stable DOM order is the tie-breaker.
  const orderedAnchors = [...anchors].sort((left, right) =>
    left.id.localeCompare(right.id),
  );

  return (
    <SceneSurfaceProvider backend={renderingBackend}>
      {clouds.map((cloud) => (
        <ProjectCloudSurface
          cloud={cloud}
          key={cloud.id}
          resourceKey={cloudPlacement.resourceKeyForCloud(cloud.id)}
          renderObject={cloud.id !== cloudPlacement.placedCloudId}
          onError={(error) => handleSurfaceError(cloud.id, error)}
          onLoading={() => handleSurfaceLoading(cloud.id)}
          onReady={(surface) => handleSurfaceReady(cloud.id, surface)}
          raycastable={cloud.visible && isGaussianSurfacePickActive(activeTool)}
          {...(editorVisible
            ? activeTool === "cloud"
              ? cloudPlacement.surfaceEventProps
              : placement.surfaceEventProps
            : {})}
        />
      ))}
      {showGrid && (
        <SceneGrid
          dark={dark}
          interactive
          placementEvents={
            activeTool === "cloud"
              ? cloudPlacement.surfaceEventProps
              : placement.surfaceEventProps
          }
        />
      )}
      <ambientLight intensity={dark ? 0.8 : 1.25} />
      <directionalLight
        castShadow
        intensity={dark ? 1.7 : 2.1}
        position={[5, 8, 4]}
        shadow-mapSize={[1024, 1024]}
      />
      {editorVisible && placement.previewHit !== null && (
        <AnchorPlacementPreview
          backend={renderingBackend}
          hit={placement.previewHit}
          label={getAnchorLabel(anchors)}
        />
      )}
      {editorVisible && pendingCloud && cloudPlacement.preview && (
        <CloudPlacementPreview
          asset={cloudPlacement.preview.asset}
          hit={cloudPlacement.preview.hit}
          resourceKey={cloudPlacement.preview.resourceKey}
        />
      )}
      {cloudPlacement.placed && (
        <CloudPlacementPreview
          asset={cloudPlacement.placed.asset}
          hit={cloudPlacement.placed.hit}
          resourceKey={cloudPlacement.placed.resourceKey}
        />
      )}
      {editorVisible &&
        orderedAnchors.map((anchor) => {
          const markerAnchor =
            heightEditing.preview?.anchorId === anchor.id
              ? {
                  ...anchor,
                  lift: heightEditing.preview.lift,
                  lift_axis: "world_up" as const,
                }
              : anchor;
          return (
            <AnchorMarker
              anchor={markerAnchor}
              hovered={heightEditing.hoveredAnchorId === anchor.id}
              key={anchor.id}
              {...heightEditing.getAnchorInteractionProps(anchor)}
              onContextMenu={(event) => {
                event.stopPropagation();
                event.nativeEvent.preventDefault();
                onOpenAnchorMenu(anchor, {
                  x: event.nativeEvent.clientX,
                  y: event.nativeEvent.clientY,
                });
              }}
            />
          );
        })}
      {editorVisible && heightEditing.activeAnchor !== null && (
        <AnchorHeightEditingOverlay
          anchor={heightEditing.activeAnchor}
          backend={renderingBackend}
          dragging={heightEditing.preview?.dragging ?? false}
          lift={heightEditing.preview?.lift ?? heightEditing.activeAnchor.lift}
        />
      )}
      <OrbitControls
        enabled={activeTool === null}
        makeDefault
        maxDistance={Infinity}
        minDistance={0.001}
        onChange={() => {
          placement.handleControlsChange();
          cloudPlacement.handleControlsChange();
        }}
        onEnd={handleOrbitEnd}
        ref={orbitControlsRef}
        target={orbitTarget}
      />
    </SceneSurfaceProvider>
  );
}
