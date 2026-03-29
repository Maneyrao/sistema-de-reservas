"use client"

import { ArrowRight } from "lucide-react"
import { BrandLoader } from "@/components/brand-loader"
import { useBooking } from "@/components/booking/booking-context"
import { slotLabel } from "@/components/booking/utils"
import { cn } from "@/lib/utils"

function groupSlotsByPeriod(slots: { start: string }[]) {
  const morning: typeof slots = []
  const afternoon: typeof slots = []
  const evening: typeof slots = []
  for (const item of slots) {
    const hour = new Date(item.start).getHours()
    if (hour < 13) morning.push(item)
    else if (hour < 18) afternoon.push(item)
    else evening.push(item)
  }
  return { morning, afternoon, evening }
}

export function TimeSlotPicker() {
  const { slots, slot, setSlot, loadingSlots, slotError, date, setDate, days } = useBooking()

  if (!date) return null

  return (
    <div className="animate-in fade-in slide-in-from-top-2 duration-300">
      <div className="mb-3 flex items-center gap-2">
        <div className="h-px flex-1 bg-zinc-800" />
        <span className="text-[10px] uppercase tracking-[0.3em] text-zinc-500">Horarios disponibles</span>
        <div className="h-px flex-1 bg-zinc-800" />
      </div>

      <div className="rounded-2xl border border-zinc-800 bg-black/30 p-4">
        {loadingSlots ? (
          <BrandLoader fullscreen={false} message="Consultando agenda..." className="bg-transparent py-4" />
        ) : slotError ? (
          <div className="py-2 text-center">
            <p className="text-sm text-red-300">{slotError}</p>
            <button
              type="button"
              onClick={() => { setDate(date) }}
              className="mt-2 text-xs text-amber-500 hover:text-amber-400 underline"
            >
              Reintentar
            </button>
          </div>
        ) : slots.length === 0 ? (
          <EmptySlots days={days} currentDate={date} setDate={setDate} />
        ) : (
          <SlotGroups slots={slots} slot={slot} setSlot={setSlot} />
        )}
      </div>
    </div>
  )
}

function EmptySlots({
  days,
  currentDate,
  setDate,
}: {
  days: { key: string; value: Date }[]
  currentDate: string
  setDate: (d: string) => void
}) {
  const nextDaysWithDate = days.filter((d) => d.key > currentDate).slice(0, 3)

  return (
    <div className="space-y-3 py-1">
      <p className="text-center text-sm text-zinc-400">Sin turnos disponibles para este día.</p>
      {nextDaysWithDate.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-center text-[10px] uppercase tracking-widest text-zinc-600">Probá con</p>
          <div className="flex justify-center gap-2">
            {nextDaysWithDate.map((d) => (
              <button
                key={d.key}
                type="button"
                onClick={() => setDate(d.key)}
                className="flex items-center gap-1.5 rounded-xl border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-300 transition hover:border-amber-500/40 hover:text-amber-400"
              >
                {d.value.toLocaleDateString("es-AR", { weekday: "short", day: "numeric" })}
                <ArrowRight className="h-3 w-3" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function SlotGroups({
  slots,
  slot,
  setSlot,
}: {
  slots: { start: string; end: string }[]
  slot: { start: string; end: string } | null
  setSlot: (s: { start: string; end: string } | null) => void
}) {
  const { morning, afternoon, evening } = groupSlotsByPeriod(slots)
  let offset = 0

  const morningStart = offset; offset += morning.length
  const afternoonStart = offset; offset += afternoon.length
  const eveningStart = offset

  return (
    <div className="space-y-4">
      <SlotGroup label="Mañana" emoji="☀️" items={morning} selected={slot} onSelect={setSlot} startIndex={morningStart} />
      <SlotGroup label="Tarde" emoji="🌤" items={afternoon} selected={slot} onSelect={setSlot} startIndex={afternoonStart} />
      <SlotGroup label="Noche" emoji="🌙" items={evening} selected={slot} onSelect={setSlot} startIndex={eveningStart} />
    </div>
  )
}

function SlotGroup({
  label, emoji, items, selected, onSelect, startIndex,
}: {
  label: string
  emoji: string
  items: { start: string; end: string }[]
  selected: { start: string; end: string } | null
  onSelect: (s: { start: string; end: string }) => void
  startIndex: number
}) {
  if (items.length === 0) return null

  return (
    <div>
      <p className="mb-2 text-[10px] uppercase tracking-[0.28em] text-zinc-500">{emoji} {label}</p>
      <div className="flex flex-wrap gap-2">
        {items.map((item, index) => (
          <button
            key={item.start}
            type="button"
            onClick={() => onSelect(item)}
            aria-pressed={selected?.start === item.start}
            style={{ animationDelay: `${(startIndex + index) * 35}ms` }}
            className={cn(
              "animate-in fade-in zoom-in-90 rounded-xl border px-3.5 py-2 text-sm font-medium transition-all duration-150 fill-mode-both",
              selected?.start === item.start
                ? "border-amber-500 bg-amber-500 text-zinc-950 shadow-md shadow-amber-500/25 scale-105"
                : "border-zinc-700 bg-zinc-900/70 text-zinc-300 hover:border-amber-500/40 hover:bg-zinc-800 hover:scale-105"
            )}
          >
            {slotLabel(item.start)}
          </button>
        ))}
      </div>
    </div>
  )
}
