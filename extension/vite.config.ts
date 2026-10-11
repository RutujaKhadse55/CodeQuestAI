import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { crx } from "@crxjs/vite-plugin";
import manifest from "./manifest.json";
import path from "path";

export default defineConfig({
  resolve: {
    alias: {
      "@locales": path.resolve(__dirname, "../shared/locales"),
    },
  },
  plugins: [react(), crx({ manifest })],
  build: {
    rollupOptions: {
      input: {
        options: "src/options/index.html",
        popup: "src/popup/index.html",
        offscreen: "src/offscreen/offscreen.html",
      },
    },
  },
});
