import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vite";

export default defineConfig(({ mode }) => ({
  plugins: [svelte()],
  server: {
    port: 5173,
  },
  resolve: {
    conditions: mode === "test" ? ["browser"] : [],
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest-setup.js"],
    globals: true,
  },
}));
