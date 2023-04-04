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
}

export interface AccountStore {
  currentAccount?: Account
  accounts?: Array<Account>
}
