export interface Account {
  counter: number
  email: string
  err: string
  id: string
  is_busy: boolean
  is_disabled: boolean
  is_logged_in: boolean
  level: number
  user?: {
    email: string
    groups: Array<any>
    id: string
    image: string
    name: string
    picture: string
  }
  history?: History
}

export interface History {
  has_missing_conversations: boolean
  items: Array<HistoryItem>
  limit: number
  offset: number
  total: number
}
export interface HistoryItem {
  create_time: string
  id: string
  title: string
  update_time: string
}

export interface AccountStore {
  currentAccount?: Account
  accounts?: Array<Account>
}

export interface ChatStore {
  history?: Array<MessageMeta>
}

export interface ChatHistory {
  create_time: string
  current_node: string
  title: string
  update_time: number
  mapping: Record<string, MessageMeta>
}

export interface MessageMeta {
  // 子节点
  children: Array<string>
  id: string
  message: MessageItem
  // 父节点
  parent?: string
}

export interface MessageItem {
  author: {
    metadata: Object
    // 用户or机器人
    role: string
  }
  content?: {
    content_type: string
    // 具体的消息内容
    parts?: Array<string>
    create_time: number
    id: string
  }
  metadata: {
    timestamp: string
  }
  recipient: string
  weight: number
}
