import { Component } from "solid-js"
import { For, Show } from "solid-js"
import { queryChatHistory } from "~/api"
import { accountStore, logout } from "~/store/account"
import { setChat } from "~/store/chat"
import { HistoryItem } from "~/types"
import { useNavigate } from "@solidjs/router"
import { ChatHistory } from "~/types"

const Item: Component<{
  historyItem: HistoryItem
}> = p => {
  function parseChatHistory(c: ChatHistory) {
    const currentNode = c.mapping[c.current_node]
    let parent: string | undefined = currentNode.parent
    const msgSort: Array<any> = [currentNode]
    while (true) {
      if (!parent) break
      const parentNode = c.mapping[parent]
      if (parentNode) {
        parentNode.message && msgSort.push(parentNode)
        parent = parentNode.parent
      }
    }
    return msgSort.reverse()
  }
  async function hdlQueryChat() {
    const _ = parseChatHistory(await queryChatHistory(accountStore.currentAccount!.id, p.historyItem.id))
    setChat({ history: _ })
  }
  return (
    <div onClick={hdlQueryChat} flex="~" title={p.historyItem.id} class="space-x-16px items-center hover:(bg-gray-900) cursor-pointer p-4 rounded-4" text="5">
      <span class="i-mdi-message-outline shrink-0 " />
      <span class="truncate">{p.historyItem.title}</span>
    </div>
  )
}

const HistoryMgr: Component = () => {
  const nav = useNavigate()
  async function hdlLogout() {
    await logout()
    nav("/login", { replace: true })
  }
  return (
    <div class="h-2/10 shrink-0 w-full overflow-scroll" flex="~ col" border="gray-600 t-1px" text="6">
      <div class="hover:(bg-gray-900) p-8 border-b-1px border-gray-700" cursor-pointer>
        删除所有聊天
      </div>
      <Show when={accountStore.currentAccount}>
        <div onClick={hdlLogout} class="hover:(bg-gray-900) p-8 border-b-1px border-gray-700" cursor-pointer>
          退出登录
        </div>
      </Show>
      <div
        onClick={() => {
          nav("/login", { replace: true })
        }}
        class="hover:(bg-gray-900) p-8 border-b-1px border-gray-700"
        cursor-pointer>
        添加账户
      </div>
    </div>
  )
}

const History: Component = () => {
  return (
    <div flex="~ col" class="h-full w-1/8 bg-gray-800 space-y-2 select-none">
      <div class="h-8/10 overflow-scroll p-4">
        <For each={accountStore.currentAccount?.history?.items}>{it => <Item historyItem={it} />}</For>
      </div>
      <HistoryMgr />
    </div>
  )
}

export default History
