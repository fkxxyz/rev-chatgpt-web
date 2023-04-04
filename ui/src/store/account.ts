import { createStore } from "solid-js/store"
import { listAccounts, queryAccountInfo } from "~/api"
import { AccountStore } from "~/types"

export const [accountStore, setAccountStore] = createStore<AccountStore>({})

export async function updateAccounts() {
  const accounts = await listAccounts()
  setAccountStore({ accounts } as AccountStore)
}

export async function updateCurrentAccount() {
  if (accountStore.accounts?.length === 0) return
  setAccountStore({ currentAccount: await queryAccountInfo(accountStore.currentAccount ? accountStore.currentAccount.id : accountStore.accounts![0].id) } as AccountStore)
}
