import { defineConfig } from "orval";

export default defineConfig({
  simulator: {
    input: "../../../backend/openapi.json",
    output: {
      clean: true,
      target: "src/shared/api/generated/client.ts",
      schemas: "src/shared/api/generated/model",
      client: "react-query",
      httpClient: "fetch",
      mode: "single",
      override: {
        mutator: {
          path: "src/shared/api/orval-fetch.ts",
          name: "orvalFetch",
        },
      },
    },
  },
});
