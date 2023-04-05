import type { Component } from "solid-js"
import { For } from "solid-js"
import AccountList from "../account/list"
import { chat, setChat } from "~/store/chat"
import { MessageMeta } from "~/types"

const MessageUser: Component<{
  msg: MessageMeta
}> = p => {
  return (
    <div flex="~" class="xyc p-8" text="left gray-300">
      <div flex="~ row" class="h-full items-center w-320 space-x-16px">
        <div flex="~" class="items-start h-full">
          <span class="i-mdi-human text-8 shrink-0" />
        </div>
        <span class="py-2">{p.msg.message.content?.parts}</span>
      </div>
    </div>
  )
}

const MessageAss: Component<{
  msg: MessageMeta
}> = p => {
  return (
    <div flex="~" class="xyc p-8 bg-slate-600" text="left slate-300">
      <div flex="~ row" class="h-full items-center w-320 space-x-16px">
        <div flex="~" class="items-start h-full">
          <span class="i-mdi-robot-happy-outline text-8 text-sky-400 shrink-0" />
        </div>
        <span class="py-2">{p.msg.message.content?.parts}</span>
      </div>
    </div>
  )
}

const Chat: Component = () => {
  return (
    <div flex="~ col" class="h-full w-full bg-gray-700 overflow-scroll" scrollbar="~ w-0 h-0">
      <AccountList />
      <div flex="~ col" text="5">
        <For each={chat?.history}>{message => (message.message.author.role == "user" ? <MessageUser msg={message} /> : <MessageAss msg={message} />)}</For>
      </div>
    </div>
  )
}

export default Chat
