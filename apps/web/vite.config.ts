import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8080,
    strictPort: true,
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  build: { target: "es2022" },
});
