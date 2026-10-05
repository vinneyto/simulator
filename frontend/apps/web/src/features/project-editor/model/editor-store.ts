import { createStore, type StoreApi } from "zustand/vanilla";
import type { LibraryAsset } from "@/shared/api/generated/model";
export type EditorTool = "anchor" | "anchor-height" | "cloud";
export type EditorHoveredObject = { id: string; type: "anchor" };
export interface EditorToolState {
  activeTool: EditorTool | null;
  hoveredObject: EditorHoveredObject | null;
  pendingCloud: LibraryAsset | null;
}
interface EditorToolActions {
  clearHoveredAnchor: (anchorId: string) => void;
  hoverAnchor: (anchorId: string) => void;
  setActiveTool: (tool: EditorTool | null) => void;
  startCloudPlacement: (asset: LibraryAsset) => void;
}
export interface EditorStore {
  tool: EditorToolState;
  toolActions: EditorToolActions;
}
export type EditorStoreApi = StoreApi<EditorStore>;
export function createEditorStore(): EditorStoreApi {
  return createStore<EditorStore>((set) => ({
    tool: { activeTool: null, hoveredObject: null, pendingCloud: null },
    toolActions: {
      clearHoveredAnchor: (anchorId) =>
        set((state) =>
          state.tool.hoveredObject?.id === anchorId
            ? { tool: { ...state.tool, hoveredObject: null } }
            : state,
        ),
      hoverAnchor: (id) =>
        set((state) => ({
          tool: { ...state.tool, hoveredObject: { id, type: "anchor" } },
        })),
      setActiveTool: (activeTool) =>
        set((state) => ({
          tool: {
            ...state.tool,
            activeTool,
            pendingCloud:
              activeTool === "cloud" ? state.tool.pendingCloud : null,
          },
        })),
      startCloudPlacement: (pendingCloud) =>
        set((state) => ({
          tool: {
            ...state.tool,
            activeTool: "cloud",
            pendingCloud: { ...pendingCloud },
          },
        })),
    },
  }));
}
