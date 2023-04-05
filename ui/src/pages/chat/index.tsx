import type { Component } from "solid-js"
import { For } from "solid-js"
import AccountList from "../account/list"
import { chat, setChat } from "~/store/chat"
import { MessageMeta } from "~/types"

const MessageUser: Component<{
  msg: MessageMeta
}> = p => {
  return (
    <div flex="~" class="xyc p-8 ">
      {p.msg.message.content?.parts}
    </div>
  )
}

const MessageAss: Component<{
  msg: MessageMeta
}> = p => {
  return (
    <div flex="~" class="xyc p-8 bg-slate-600">
      {p.msg.message.content?.parts}
    </div>
  )
}

const Chat: Component = () => {
  return (
    <div flex="~ col" class="h-full w-full bg-gray-700">
      <AccountList />
      <div flex="~ col" text="5">
        <For each={chat?.history}>{message => (message.message.author.role == "user" ? <MessageUser msg={message} /> : <MessageAss msg={message} />)}</For>
      </div>
    </div>
  )
}

export default Chat
