"use client"

import { Check, CalendarDays, Clock3, User, Phone, Instagram, MapPin } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { useBooking } from "@/components/booking/booking-context"
import { formatCurrency, formatLongDate, initialsFromName } from "@/components/booking/utils"

export function BookingConfirmation() {
  const { catalog, confirmedBooking, selectedStaff, selectedService, resetBooking } = useBooking()
  if (!confirmedBooking || !catalog || !selectedStaff || !selectedService) return null

  return (
    <div className="animate-in fade-in zoom-in-95 space-y-4 duration-500">
      {/* Check de éxito */}
      <div className="flex flex-col items-center gap-3 py-6 text-center">
        <div className="flex h-16 w-16 animate-in zoom-in-50 items-center justify-center rounded-full bg-emerald-500/15 duration-500 delay-150">
          <Check className="h-8 w-8 text-emerald-400" strokeWidth={2.5} />
        </div>
        <div className="animate-in fade-in slide-in-from-bottom-2 duration-500 delay-300">
          <p className="text-xs uppercase tracking-[0.4em] text-emerald-400/80">Reserva confirmada</p>
          <h2 className="mt-1 font-display text-4xl uppercase leading-none">Turno registrado</h2>
          <p className="mt-2 text-sm text-zinc-400">
            Te esperamos en {catalog.business.name}. La coordinación final por WhatsApp.
          </p>
        </div>
      </div>

      {/* Resumen del turno */}
      <div className="animate-in fade-in slide-in-from-bottom-3 space-y-2 duration-500 delay-[400ms]">
        <div className="rounded-2xl border border-zinc-800 bg-black/30 p-4">
          <div className="flex items-center gap-3">
            <Avatar className="h-11 w-11 border border-amber-500/20">
              <AvatarImage src={selectedStaff.avatar_url || undefined} alt={selectedStaff.name} />
              <AvatarFallback className="bg-zinc-800 text-sm">{initialsFromName(selectedStaff.name)}</AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <p className="font-semibold">{selectedStaff.name}</p>
              <p className="text-sm text-amber-400">{selectedService.name}</p>
            </div>
            <p className="shrink-0 text-sm font-semibold text-amber-300">
              {formatCurrency(selectedService.price_amount, selectedService.price_currency)}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className="rounded-2xl border border-zinc-800 bg-black/30 p-3">
            <div className="flex items-center gap-2 text-zinc-500">
              <CalendarDays className="h-3.5 w-3.5" />
              <span className="text-[10px] uppercase tracking-wider">Fecha y hora</span>
            </div>
            <p className="mt-1.5 text-sm font-medium leading-snug">
              {formatLongDate(confirmedBooking.start_datetime)}
            </p>
          </div>
          <div className="rounded-2xl border border-zinc-800 bg-black/30 p-3">
            <div className="flex items-center gap-2 text-zinc-500">
              <Clock3 className="h-3.5 w-3.5" />
              <span className="text-[10px] uppercase tracking-wider">Duración</span>
            </div>
            <p className="mt-1.5 text-sm font-medium">{selectedService.duration_minutes} minutos</p>
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-black/30 p-3">
          <div className="flex items-center gap-2 text-zinc-500">
            <User className="h-3.5 w-3.5" />
            <span className="text-[10px] uppercase tracking-wider">A nombre de</span>
          </div>
          <p className="mt-1.5 text-sm font-medium">{confirmedBooking.customer_name}</p>
        </div>
      </div>

      {/* Contacto rápido */}
      {(catalog.business.phone || catalog.business.address || catalog.business.instagram_url) && (
        <div className="animate-in fade-in duration-500 delay-500 space-y-2">
          <div className="flex items-center gap-2">
            <div className="h-px flex-1 bg-zinc-800" />
            <span className="text-[10px] uppercase tracking-[0.3em] text-zinc-600">Dónde encontrarnos</span>
            <div className="h-px flex-1 bg-zinc-800" />
          </div>
          <div className="rounded-2xl border border-zinc-800 bg-black/30 p-3 space-y-2.5">
            {catalog.business.phone && (
              <a href={`tel:${catalog.business.phone}`} className="flex items-center gap-2.5 text-sm text-zinc-400 transition hover:text-amber-400">
                <Phone className="h-3.5 w-3.5 shrink-0 text-amber-500/60" />{catalog.business.phone}
              </a>
            )}
            {catalog.business.address && (
              <a href={catalog.business.maps_url || "#"} target="_blank" rel="noreferrer" className="flex items-center gap-2.5 text-sm text-zinc-400 transition hover:text-amber-400">
                <MapPin className="h-3.5 w-3.5 shrink-0 text-amber-500/60" />{catalog.business.address}
              </a>
            )}
            {catalog.business.instagram_url && (
              <a href={catalog.business.instagram_url} target="_blank" rel="noreferrer" className="flex items-center gap-2.5 text-sm text-zinc-400 transition hover:text-amber-400">
                <Instagram className="h-3.5 w-3.5 shrink-0 text-amber-500/60" />@clubamsterdam_
              </a>
            )}
          </div>
        </div>
      )}

      {/* CTA */}
      <Button
        type="button"
        onClick={resetBooking}
        className="w-full animate-in fade-in rounded-2xl bg-amber-500 font-semibold text-zinc-950 duration-500 delay-[600ms] hover:bg-amber-400 hover:shadow-lg hover:shadow-amber-500/20 active:scale-95"
      >
        Reservar otro turno
      </Button>
    </div>
  )
}
