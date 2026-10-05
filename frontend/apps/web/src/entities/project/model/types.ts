import type * as Api from "@/shared/api/generated/model";

export type Vec3 = Api.Anchor["surface_position"];
export type Anchor = Required<Api.Anchor>;
export type ScenePoint = Required<Api.ScenePoint>;
export type AnchorCreate = Api.AnchorCreate;
export type AnchorUpdate = Api.AnchorUpdate;
export interface Project extends Api.ProjectMetadata {
  anchors: Record<string, Anchor>;
  scene_points: Record<string, ScenePoint>;
}
