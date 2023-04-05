import type { Component } from "solid-js"
import { onMount } from "solid-js"
import Index from "./pages"
import { accountStore } from "./store/account"
import { updateAccounts, updateCurrentAccount } from "./store/account"
import { Router, useRoutes } from "@solidjs/router"
import routes from "~/router"

const RouterView = useRoutes(routes, "/")
const App: Component = () => {
  onMount(async () => {
    await updateAccounts()
    await updateCurrentAccount()
  })
  return (
    <div class="h-screen w-screen " text="white 16px" font-semibold>
      <Router>
        <RouterView />
      </Router>
    </div>
  )
}

export default App
