import type { Component } from "solid-js"
import { createSignal, Show } from "solid-js"
import { loginBySesison } from "~/api"
import { updateAccounts, updateCurrentAccount } from "~/store/account"
import Button from "~/widget/button"

const [token, setToken] = createSignal("")

const [msg, setMsg] = createSignal("")

async function hdlLogin() {
  setMsg("登录中...")
  if (await loginBySesison(token())) {
    setMsg("登录成功")
    await updateAccounts()
    await updateCurrentAccount()
  } else {
    setMsg("登录失败")
  }
}

const Form: Component = () => {
  return (
    <div flex="~ col" class="rounded-20px bg-white space-y-16px" w-120 h-fit p-10 text="#333">
      <div flex="~ col" grow>
        <input
          class="h-full"
          border="~ 1px blue"
          rounded-2
          placeholder="请输入SessionJSON"
          type="text"
          value={token()}
          onChange={(e: any) => {
            e.target.value === "" && setMsg("")
            setToken(e.target.value)
          }}
        />
      </div>
      <div flex="~ col" justify-end space-y-16px>
        <Button click={hdlLogin} title="登录" />
        <Show when={msg() != ""}>
          <span w-full text="center blue">
            {msg()}
          </span>
        </Show>
      </div>
    </div>
  )
}
const Login: Component = () => {
  return (
    <div flex="~" class="xyc w-full h-full bg-#715fde">
      <Form />
    </div>
  )
}

export default Login
