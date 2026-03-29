import { cn } from "@/lib/utils"

export function formatDateValue(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`
}

export function nextDays(total: number) {
  return Array.from({ length: total }, (_, index) => {
    const date = new Date()
    date.setHours(0, 0, 0, 0)
    date.setDate(date.getDate() + index)
    return { key: formatDateValue(date), value: date }
  })
}

export function slotLabel(iso: string) {
  return new Date(iso).toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit", hour12: false })
}

export function formatLongDate(iso: string) {
  return new Date(iso).toLocaleString("es-AR", { weekday: "long", day: "numeric", month: "long", hour: "2-digit", minute: "2-digit", hour12: false })
}

export function formatCurrency(amount: number, currency: string) {
  return new Intl.NumberFormat("es-AR", { style: "currency", currency, maximumFractionDigits: 0 }).format(amount)
}

export function initialsFromName(name: string) {
  return name.split(" ").filter(Boolean).slice(0, 2).map((value) => value[0]?.toUpperCase() ?? "").join("")
}

export function inputClasses(invalid = false) {
  return cn("w-full rounded-2xl border bg-black/40 px-4 py-3 text-sm text-zinc-50 outline-none transition-all", invalid ? "border-red-500/70 focus:border-red-500" : "border-amber-500/15 focus:border-amber-500 focus:bg-black/70")
}

export function buildMapEmbedUrl(value: string | null) {
  if (!value) return null
  const match = value.match(/q=([^&]+)/)
  return match?.[1] ? `https://maps.google.com/maps?q=${match[1]}&z=15&output=embed` : null
}

export function tone(index: number) {
  return ["from-amber-500/22 via-amber-500/8 to-black", "from-zinc-100/8 via-amber-500/10 to-black", "from-amber-300/16 via-amber-500/8 to-black", "from-zinc-200/10 via-zinc-900 to-black"][index % 4]
}
