import type { Component } from "solid-js"
import History from "./history"
import Chat from "./chat"
import { onMount } from "solid-js"
import Login from "~/pages/account/login"
import { useNavigate } from "@solidjs/router"
import { accountStore } from "~/store/account"

const Index: Component = () => {
  const nav = useNavigate()
  onMount(() => {
    if (accountStore.accounts?.length === 0) {
      nav("/login", { replace: true })
    }
  })
  return (
    <div flex="~ row" h-full w-full>
      <History />
      <Chat />
    </div>
  )
}

export default Index
