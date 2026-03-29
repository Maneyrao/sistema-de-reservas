"use client"

import { LogOut } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { type DashboardTab, useAdminContext } from "./admin-context"

export function Sidebar() {
  const { business, adminUser, activeTab, setActiveTab, logout } = useAdminContext()

  return (
    <Card className="overflow-hidden border-amber-500/15 bg-zinc-900/90">
      <CardContent className="flex flex-col gap-6 p-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-4">
          <img
            src="/club-amsterdam-monogram.svg"
            alt="Club Amsterdam"
            className="h-20 w-20 rounded-2xl border border-amber-500/15 bg-black/35 p-2"
          />
          <div>
            <p className="text-xs uppercase tracking-[0.45em] text-amber-500/75">Dashboard Owner</p>
            <h1 className="font-display text-6xl uppercase leading-none">{business?.name || "Club Amsterdam"}</h1>
            <p className="mt-2 text-sm text-zinc-400">
              {adminUser?.full_name} · {adminUser?.email}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          {(["agenda", "staff", "services", "business", "blocks"] as DashboardTab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                "rounded-full border px-4 py-2 text-sm uppercase tracking-[0.2em] transition",
                activeTab === tab
                  ? "border-amber-500 bg-amber-500 text-zinc-950"
                  : "border-zinc-800 bg-black/30 text-zinc-300 hover:border-amber-500/30",
              )}
            >
              {tab}
            </button>
          ))}
          <Button variant="outline" onClick={logout} className="border-zinc-700 bg-transparent text-zinc-300">
            <LogOut className="mr-2 h-4 w-4" />
            Salir
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
