"use client"

import { Scissors } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useBooking } from "@/components/booking/booking-context"
import { initialsFromName } from "@/components/booking/utils"
import { cn } from "@/lib/utils"

export function StaffSelector() {
  const { catalog, selectedStaff, setSelectedStaffSlug, setSlot } = useBooking()
  if (!catalog || !selectedStaff) return null

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm uppercase tracking-[0.25em] text-zinc-500">
        <Scissors className="h-4 w-4 text-amber-500" />Barberos disponibles
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {catalog.staff.map((item, index) => (
          <button
            key={item.slug}
            onClick={() => { setSelectedStaffSlug(item.slug); setSlot(null) }}
            style={{ animationDelay: `${index * 80}ms` }}
            className={cn(
              "animate-in fade-in slide-in-from-bottom-3 rounded-2xl border p-4 text-left transition-all duration-200 fill-mode-both",
              selectedStaff.slug === item.slug
                ? "border-amber-500 bg-black/55 shadow-lg shadow-amber-500/10 scale-[1.01]"
                : "border-zinc-800 bg-black/20 hover:border-amber-500/30 hover:bg-black/35 hover:scale-[1.01]"
            )}
          >
            <div className="flex items-center gap-3">
              <Avatar className="h-12 w-12 border border-amber-500/15">
                <AvatarImage src={item.avatar_url || undefined} alt={item.name} />
                <AvatarFallback className="bg-zinc-800 text-zinc-100 text-sm">{initialsFromName(item.name)}</AvatarFallback>
              </Avatar>
              <div>
                <p className="font-semibold">{item.name}</p>
                <p className="text-sm text-amber-400">{item.title || "Barber"}</p>
              </div>
            </div>
            {item.bio ? <p className="mt-3 text-sm leading-5 text-zinc-400">{item.bio}</p> : null}
          </button>
        ))}
      </div>
    </div>
  )
}
