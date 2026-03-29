"use client"

import { Sparkles } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { useBooking } from "@/components/booking/booking-context"
import { formatCurrency, tone } from "@/components/booking/utils"
import { cn } from "@/lib/utils"

export function ServiceSelector() {
  const { availableServices, selectedService, selectedStaff, setSelectedServiceSlug, setSlot } = useBooking()
  if (!selectedStaff || !selectedService) return null

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm uppercase tracking-[0.25em] text-zinc-500">
        <Sparkles className="h-4 w-4 text-amber-500" />Servicios para {selectedStaff.name}
      </div>
      {availableServices.length === 0 ? (
        <div className="rounded-2xl border border-zinc-800 bg-black/25 p-4 text-sm text-zinc-400">
          Este barbero todavía no tiene servicios activos asignados.
        </div>
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {availableServices.map((item, index) => (
            <button
              key={item.slug}
              onClick={() => { setSelectedServiceSlug(item.slug); setSlot(null) }}
              style={{ animationDelay: `${index * 80 + 160}ms` }}
              className={cn(
                "animate-in fade-in slide-in-from-bottom-3 rounded-2xl border bg-gradient-to-br p-4 text-left transition-all duration-200 fill-mode-both",
                tone(index),
                selectedService.slug === item.slug
                  ? "border-amber-500 shadow-lg shadow-amber-500/10 scale-[1.01]"
                  : "border-zinc-800 hover:border-amber-500/30 hover:scale-[1.01]"
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">{item.name}</p>
                  <p className="mt-1 text-sm text-zinc-300">{item.duration_minutes} min</p>
                </div>
                <Badge className="rounded-full bg-black/35 px-3 py-1 text-amber-300 shrink-0">
                  {formatCurrency(item.price_amount, item.price_currency)}
                </Badge>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
