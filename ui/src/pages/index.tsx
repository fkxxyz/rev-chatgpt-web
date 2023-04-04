import type { Component } from "solid-js"
import History from "./history"
import Chat from "./chat"

const Index: Component = () => {
  return (
    <div flex="~ row" h-full w-full>
      <History />
      <Chat />
    </div>
  )
}

export default Index
