"use client"

import { Scissors, Shuffle } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { useBooking } from "@/components/booking/booking-context"
import { initialsFromName } from "@/components/booking/utils"
import { cn } from "@/lib/utils"

export function StaffSelector() {
  const { catalog, selectedStaff, setSelectedStaffSlug, setSlot } = useBooking()
  if (!catalog || !selectedStaff) return null

  const defaultSlug = catalog.booking_rules.default_staff_slug || catalog.staff[0]?.slug
  const isAny = !catalog.staff.some((s) => s.slug === selectedStaff.slug && selectedStaff.slug !== defaultSlug)

  function selectAny() {
    setSelectedStaffSlug(defaultSlug)
    setSlot(null)
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.25em] text-zinc-500">
        <Scissors className="h-3.5 w-3.5 text-amber-500" />Barberos disponibles
      </div>

      {/* Opción "sin preferencia" */}
      <button
        type="button"
        onClick={selectAny}
        className={cn(
          "w-full rounded-2xl border px-4 py-3 text-left transition-all duration-200",
          "flex items-center gap-3",
          selectedStaff.slug === defaultSlug && catalog.staff.length > 1
            ? "border-amber-500/40 bg-amber-500/5"
            : "border-zinc-800 bg-black/20 hover:border-amber-500/20 hover:bg-black/30"
        )}
      >
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-zinc-800">
          <Shuffle className="h-4 w-4 text-zinc-400" />
        </div>
        <div>
          <p className="text-sm font-medium text-zinc-200">Sin preferencia</p>
          <p className="text-xs text-zinc-500">El sistema asigna el barbero disponible</p>
        </div>
      </button>

      <div className="grid gap-2 md:grid-cols-2">
        {catalog.staff.map((item, index) => (
          <button
            key={item.slug}
            type="button"
            onClick={() => { setSelectedStaffSlug(item.slug); setSlot(null) }}
            style={{ animationDelay: `${index * 80}ms` }}
            aria-pressed={selectedStaff.slug === item.slug}
            className={cn(
              "animate-in fade-in slide-in-from-bottom-3 rounded-2xl border p-4 text-left transition-all duration-200 fill-mode-both",
              selectedStaff.slug === item.slug
                ? "border-amber-500 bg-black/55 shadow-lg shadow-amber-500/10 scale-[1.01]"
                : "border-zinc-800 bg-black/20 hover:border-amber-500/30 hover:bg-black/35 hover:scale-[1.01]"
            )}
          >
            <div className="flex items-center gap-3">
              <Avatar className="h-11 w-11 border border-amber-500/15">
                <AvatarImage src={item.avatar_url || undefined} alt={item.name} />
                <AvatarFallback className="bg-zinc-800 text-zinc-100 text-xs">{initialsFromName(item.name)}</AvatarFallback>
              </Avatar>
              <div className="min-w-0">
                <p className="font-semibold leading-tight">{item.name}</p>
                <p className="mt-0.5 text-xs text-amber-400">{item.title || "Barber"}</p>
              </div>
            </div>
            {item.bio ? (
              <p className="mt-2.5 line-clamp-2 text-xs leading-5 text-zinc-400">{item.bio}</p>
            ) : null}
          </button>
        ))}
      </div>
    </div>
  )
}
