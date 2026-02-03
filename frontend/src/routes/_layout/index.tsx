import { createFileRoute } from "@tanstack/react-router"

import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
  head: () => ({
    meta: [
      {
        title: "Dashboard - FastAPI Cloud",
      },
    ],
  }),
})

function Dashboard() {
  const { user: currentUser } = useAuth()

  return (
    <div>
      <div>
        <h1 className="text-2xl truncate max-w-sm">
          你好, {currentUser?.full_name || currentUser?.email} 👋
        </h1>
        <p className="text-muted-foreground">
          欢迎回来，很高兴再次见到你！！！
        </p>
      </div>
    </div>
  )
}
