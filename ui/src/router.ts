import { lazy } from "solid-js"

const routes = [
  {
    path: "/",
    component: lazy(() => import("~/pages/index")),
  },
  {
    path: "/login",
    component: lazy(() => import("~/pages/account/login")),
  },
]

export default routes
