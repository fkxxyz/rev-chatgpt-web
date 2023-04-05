/* @refresh reload */
import "virtual:uno.css"
import { render } from "solid-js/web"
import "@unocss/reset/tailwind-compat.css"
import { Router } from "@solidjs/router"
const root = document.getElementById("root")
import App from "./App"

if (import.meta.env.DEV && !(root instanceof HTMLElement)) {
  throw new Error("Root element not found. Did you forget to add it to your index.html? Or maybe the id attribute got mispelled?")
}

render(() => <App />, root!)
