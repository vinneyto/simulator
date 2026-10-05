import * as api from "@/shared/api/generated/client";
import type { AnchorCreate, AnchorUpdate } from "@/shared/api/generated/model";
import {
  rememberProjectRevision,
  forgetProjectRevision,
} from "@/shared/api/orval-fetch";

// The generated client owns all HTTP paths and payloads. These small wrappers expose
// successful response bodies to the editor's existing feature hooks.
export const projectApi = {
  create: async (name: string) => {
    const response = await api.createProject({ name });
    if (response.status !== 201) throw new Error("Could not create project");
    rememberProjectRevision(response.data.id, response.data.revision);
    return response.data;
  },
  delete: async (id: string) => {
    await api.deleteProject(id);
    forgetProjectRevision(id);
  },
  addAnchor: async (id: string, anchor: AnchorCreate) =>
    (await api.createAnchor(id, anchor)).data,
  updateAnchor: async (id: string, anchorId: string, anchor: AnchorUpdate) =>
    (await api.updateAnchor(id, anchorId, anchor)).data,
  deleteAnchor: async (id: string, anchorId: string) => {
    await api.deleteAnchor(id, anchorId);
  },
};
