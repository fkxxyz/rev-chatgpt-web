import axios from "axios"
import { Account } from "../types"

const c = axios.create({
  baseURL: "api/",
})

export async function loginBySesison(session: string): Promise<Account> {
  return c
    .post("account", session, {
      headers: {
        "Content-Type": "application/json",
      },
    })
    .then(resp => resp.data)
    .catch(err => {
      console.error(err)
    })
}

export async function listAccounts(): Promise<Array<Account>> {
  return (await c.get("account/list")).data
}

export async function queryAccountInfo(id: string): Promise<Account> {
  return (await c.get(`account?account=${id}`)).data
}

export async function listAccountHistory(id: string, limit = 0, offset = 0) {
  return (await c.get(`conversations?account=${id}&limit=${limit}&offset=${offset}`)).data
}

export async function logout(id: string) {
  return (await c.delete(`account?account=${id}`)).data
}

export async function queryChatHistory(account_id: string, id: string) {
  return (await c.get(`history?account=${account_id}&id=${id}`)).data
}
