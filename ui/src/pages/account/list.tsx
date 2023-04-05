import { Component, createSignal } from "solid-js"
import { For, Show } from "solid-js"
import { accountStore, setAccountStore, updateCurrentAccount, updateAccounts, deleteAccount } from "~/store/account"
import { logout } from "~/api"
import { Account, AccountStore } from "~/types"
import { useNavigate } from "@solidjs/router"
const AccountItem: Component<{
  account: Account
}> = p => {
  const nav = useNavigate()
  const [hover, setHover] = createSignal(false)
  function changeCurrentAccount() {
    setAccountStore({ currentAccount: p.account } as AccountStore)
    updateCurrentAccount()
  }

  async function hdlDelete() {
    await deleteAccount(p.account.id)
    accountStore.accounts?.length === 0 && nav("/", { replace: true })
  }

  return (
    <div onClick={changeCurrentAccount}>
      <div
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        flex="~ row"
        class="items-center h-full p-2 rounded-12px space-x-8px cursor-pointer bg-gray-500 hover:(bg-gray-500/35) active:(bg-purple/20)">
        {hover()}
        <span shrink-0>{p.account.is_busy}</span>
        <span max-w-32 class="truncate">
          {p.account.id}
        </span>
        <Show when={hover()}>
          <div onClick={hdlDelete} class="i-mdi-close" />
        </Show>
      </div>
    </div>
  )
}

const AccountList: Component = () => {
  return (
    <div class="w-full h-fit bg-gray-600 select-none" flex="~ row">
      <div flex="~ row " class="p-4 space-x-16px shrink-0">
        <h3 shrink-0>账户管理</h3>
        <div flex="~ row">{accountStore.currentAccount?.id}</div>
      </div>

      <div flex="~ row" h-full w-full class="space-x-16px items-center">
        {/* <For each={accountStore.accounts?.concat(accountStore.accounts).concat(accountStore.accounts)}>{(it: Account) => <AccountItem account={it} />}</For> */}
        <For each={accountStore.accounts?.filter(it => it.id != accountStore.currentAccount?.id)}>{(it: Account) => <AccountItem account={it} />}</For>
      </div>
    </div>
  )
}

export default AccountList
