import { createStore } from "solid-js/store"
import { MessageMeta, ChatStore } from "~/types"

export const [chat, setChat] = createStore<ChatStore>({} as ChatStore)
