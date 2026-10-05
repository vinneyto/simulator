"use client";

import { RenderPipelineCanvas } from "@/shared/three";

import { SceneContents } from "./scene-contents";
import { SceneViewportFrame } from "./scene-viewport-frame";
import type { SceneViewportProps } from "./scene-viewport-types";
import { useWebGpuAvailability } from "./use-webgpu-availability";

export function SceneWebGpuViewport(props: SceneViewportProps) {
  const webGpuAvailable = useWebGpuAvailability();

  return (
    <SceneViewportFrame
      available={webGpuAvailable}
      clouds={props.clouds}
      onDeleteAnchor={props.onDeleteAnchor}
      renderScene={(context) => (
        <RenderPipelineCanvas
          camera={{ far: 100, fov: 42, near: 0.01, position: [4, 3, 6] }}
          dpr={[1, 2]}
          flat
          shadows
          style={{
            backgroundColor: `rgb(${context.background
              .slice(0, 3)
              .map((channel) => Math.round(channel * 255))
              .join(" ")})`,
          }}
        >
          <SceneContents
            anchors={props.anchors}
            clouds={props.clouds}
            initialCloudIds={props.initialCloudIds}
            background={context.background}
            dark={context.dark}
            onAddAnchor={props.onAddAnchor}
            onAddCloud={props.onAddCloud}
            onOpenAnchorMenu={context.onOpenAnchorMenu}
            onSurfaceError={context.onSurfaceError}
            onSurfaceLoading={context.onSurfaceLoading}
            onSurfaceReady={context.onSurfaceReady}
            onUpdateAnchorLift={props.onUpdateAnchorLift}
          />
        </RenderPipelineCanvas>
      )}
      unavailableMessage="WebGPU is unavailable in this browser"
    />
  );
}
