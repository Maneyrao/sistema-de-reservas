"use client"

import { useBooking } from "@/components/booking/booking-context"
import { cn } from "@/lib/utils"

export function DatePicker() {
  const { days, date, setDate, setSlot } = useBooking()

  return (
    <div className="grid grid-cols-5 gap-2">
      {days.map((item, index) => {
        const isSelected = date === item.key
        const isToday = index === 0
        const weekday = item.value.toLocaleDateString("es-AR", { weekday: "short" })
        const month = item.value.toLocaleDateString("es-AR", { month: "short" })

        return (
          <button
            key={item.key}
            onClick={() => { setDate(item.key); setSlot(null) }}
            style={{ animationDelay: `${index * 40}ms` }}
            className={cn(
              "animate-in fade-in zoom-in-90 relative flex flex-col items-center rounded-2xl border px-2 py-3 text-center transition-all duration-200 fill-mode-both",
              isSelected
                ? "border-amber-500 bg-amber-500 text-zinc-950 shadow-lg shadow-amber-500/25 scale-105"
                : "border-zinc-800 bg-black/25 text-zinc-300 hover:border-amber-500/40 hover:bg-zinc-800/60 hover:scale-105"
            )}
          >
            {isToday && !isSelected && (
              <span className="absolute -top-1.5 left-1/2 -translate-x-1/2 rounded-full bg-amber-500/25 px-1.5 py-px text-[8px] uppercase tracking-widest text-amber-400">hoy</span>
            )}
            <span className="text-[9px] uppercase tracking-widest opacity-70">{weekday}</span>
            <span className="mt-1 text-xl font-bold leading-none">{item.value.getDate()}</span>
            <span className={cn("mt-1 text-[9px] uppercase tracking-wide", isSelected ? "text-zinc-800" : "text-zinc-600")}>{month}</span>
          </button>
        )
      })}
    </div>
  )
}
