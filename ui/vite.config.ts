import { defineConfig } from "vite"
import UnoCSS from "unocss/vite"
import solidPlugin from "vite-plugin-solid"
import path from "path"

export default defineConfig({
  plugins: [solidPlugin(), UnoCSS()],
  resolve: {
    alias: {
      "~": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:9987",
        secure: false,
        rewrite: (path: string) => {
          console.log("path:", path)
          return path
        },
      },
    },
  },
  build: {
    target: "esnext",
  },
})
