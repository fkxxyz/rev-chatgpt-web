import axios from "axios"
import { Account } from "../types"

const c = axios.create({
  baseURL: "api/",
})

export async function loginBySesison(session: string) {
  return c
    .post("account", session, {
      headers: {
        "Content-Type": "application/json",
      },
    })
    .then(() => true)
    .catch(err => {
      console.log("login failed:", err)
      return false
    })
}

export async function listAccounts(): Promise<Array<Account>> {
  return (await c.get("account/list")).data
}

export async function queryAccountInfo(id: string): Promise<Account> {
  return (await c.get(`account?account=${id}`)).data
}
