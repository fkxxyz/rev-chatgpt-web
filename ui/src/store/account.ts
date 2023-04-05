import { createStore } from "solid-js/store"
import { listAccounts, listAccountHistory, queryAccountInfo, logout as logoutAccount } from "~/api"
import { AccountStore } from "~/types"
import { useNavigate } from "@solidjs/router"

export const [accountStore, setAccountStore] = createStore<AccountStore>({})

export async function updateAccounts() {
  const accounts = await listAccounts()
  setAccountStore({ accounts } as AccountStore)
}

export async function updateCurrentAccount() {
  if (accountStore.accounts?.length === 0) return
  let account = accountStore.currentAccount || accountStore.accounts!.at(0)!
  console.log("account:id", account.id)
  let newAccount = await queryAccountInfo(account.id)
  newAccount.history = await listAccountHistory(newAccount.id)
  setAccountStore({ currentAccount: newAccount } as AccountStore)
}

/**
 * 退出当前登录的帐号
 **/
export async function logout() {
  if (!accountStore.currentAccount?.id) return false
  await logoutAccount(accountStore.currentAccount!.id)
  await updateAccounts()
  setAccountStore({ currentAccount: undefined } as AccountStore)
  await updateCurrentAccount()
}

/**
 * 删除指定用户
 * @id 用户id
 **/
export async function deleteAccount(id: string) {
  await logoutAccount(id)
  await updateAccounts()
  setAccountStore({ currentAccount: undefined } as AccountStore)
  await updateCurrentAccount()
}
