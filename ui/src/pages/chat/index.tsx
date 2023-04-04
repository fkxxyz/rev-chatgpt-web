import type { Component } from "solid-js"
import AccountList from "../account/list"
const Chat: Component = () => {
  return (
    <div flex="~ col" class="h-full w-full bg-#715fde">
      <AccountList />
      <div flex="~ col"></div>
    </div>
  )
}

export default Chat
