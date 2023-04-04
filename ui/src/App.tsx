import type { Component } from "solid-js"
import { onMount } from "solid-js"
import Login from "./pages/account/login"
import Index from "./pages"
import { accountStore, updateAccounts, updateCurrentAccount } from "./store/account"

const App: Component = () => {
  onMount(async () => {
    await updateAccounts()
    await updateCurrentAccount()
  })
  return (
    <div class="h-screen w-screen " text="white 16px" font-semibold>
      {accountStore.accounts?.length === 0 ? <Login /> : <Index />}
    </div>
  )
}

export default App
