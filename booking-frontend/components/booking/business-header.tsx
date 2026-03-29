"use client"

import { Instagram, MapPin, Phone } from "lucide-react"
import { useBooking } from "@/components/booking/booking-context"

export function BusinessHeader() {
  const { catalog } = useBooking()
  if (!catalog) return null

  return (
    <section className="relative overflow-hidden border-b border-amber-500/10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(225,177,44,0.18),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(225,177,44,0.08),_transparent_25%)]" />
      <div className="relative mx-auto max-w-7xl px-4 py-8 lg:py-12">
        {catalog.business.announcement ? <div className="mb-6 inline-flex rounded-full border border-amber-500/20 bg-amber-500/10 px-4 py-2 text-xs uppercase tracking-[0.32em] text-amber-300">{catalog.business.announcement}</div> : null}
        <div className="grid gap-8 lg:grid-cols-[1.15fr,0.85fr]">
          <div className="space-y-6">
            <div className="flex items-center gap-4"><img src="/club-amsterdam-monogram.svg" alt="Club Amsterdam" className="h-16 w-16 rounded-2xl border border-amber-500/15 bg-black/35 p-2 sm:h-20 sm:w-20" /><div><p className="text-xs uppercase tracking-[0.45em] text-amber-500/80">Reservas Online</p><h1 className="font-display text-6xl uppercase leading-none sm:text-7xl">{catalog.business.name}</h1></div></div>
            <div><h2 className="max-w-4xl font-display text-4xl uppercase leading-none text-zinc-100 sm:text-6xl">{catalog.business.hero_title || catalog.business.tagline || "Experiencia premium en cada corte"}</h2><p className="mt-5 max-w-3xl text-base leading-7 text-zinc-300 sm:text-lg">{catalog.business.hero_description || "Reservá en segundos y caé con tu lugar asegurado en la agenda real del local."}</p></div>
            <div className="flex flex-wrap gap-3 text-sm text-zinc-300">{catalog.business.address ? <a href={catalog.business.maps_url || "#"} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-full border border-amber-500/15 bg-black/30 px-4 py-2 transition hover:border-amber-500/35 hover:text-amber-300"><MapPin className="h-4 w-4 text-amber-500" />{catalog.business.address}</a> : null}{catalog.business.phone ? <a href={`tel:${catalog.business.phone}`} className="inline-flex items-center gap-2 rounded-full border border-amber-500/15 bg-black/30 px-4 py-2 transition hover:border-amber-500/35 hover:text-amber-300"><Phone className="h-4 w-4 text-amber-500" />{catalog.business.phone}</a> : null}{catalog.business.instagram_url ? <a href={catalog.business.instagram_url} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-full border border-amber-500/15 bg-black/30 px-4 py-2 transition hover:border-amber-500/35 hover:text-amber-300"><Instagram className="h-4 w-4 text-amber-500" />@clubamsterdam_</a> : null}</div>
          </div>
          <div className="grid gap-3 rounded-[2rem] border border-amber-500/15 bg-black/30 p-4 text-sm text-zinc-300 sm:grid-cols-3 lg:grid-cols-1"><div className="rounded-2xl border border-zinc-800 bg-black/30 p-4"><p className="text-xs uppercase tracking-[0.28em] text-zinc-500">Reserva</p><p className="mt-2 font-semibold text-zinc-100">Directa sobre agenda real</p></div><div className="rounded-2xl border border-zinc-800 bg-black/30 p-4"><p className="text-xs uppercase tracking-[0.28em] text-zinc-500">Pago</p><p className="mt-2 font-semibold text-zinc-100">Luego del corte</p></div><div className="rounded-2xl border border-zinc-800 bg-black/30 p-4"><p className="text-xs uppercase tracking-[0.28em] text-zinc-500">Confirmación</p><p className="mt-2 font-semibold text-zinc-100">{catalog.business.booking_note || "WhatsApp manual y trato directo"}</p></div></div>
        </div>
      </div>
    </section>
  )
}
