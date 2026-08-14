import path from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Port 5173 is not incidental: the backend's CORS allow_origins list in
// app/main.py names it explicitly, so changing it here means changing it there.
export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  server: { port: 5173, strictPort: true },
});
