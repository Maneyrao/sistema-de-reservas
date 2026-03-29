"use client"

import { Check, Instagram, MapPin, Phone } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { useBooking } from "@/components/booking/booking-context"
import { formatLongDate, initialsFromName } from "@/components/booking/utils"

export function BookingConfirmation() {
  const { catalog, confirmedBooking, selectedStaff, selectedService } = useBooking()
  if (!confirmedBooking || !catalog || !selectedStaff || !selectedService) return null

  return (
    <div className="min-h-screen bg-zinc-950 px-6 py-10 text-zinc-50">
      <div className="mx-auto max-w-5xl">
        <Card className="overflow-hidden border-amber-500/20 bg-zinc-900/90">
          <CardContent className="grid gap-6 p-8 lg:grid-cols-[1.05fr,0.95fr]">
            <div className="space-y-6">
              <div className="flex h-20 w-20 items-center justify-center rounded-full bg-emerald-500/10"><Check className="h-10 w-10 text-emerald-400" /></div>
              <div>
                <p className="text-xs uppercase tracking-[0.45em] text-amber-500/70">Reserva registrada</p>
                <h1 className="mt-3 font-display text-6xl uppercase leading-none">Turno confirmado</h1>
                <p className="mt-4 max-w-xl text-zinc-400">Tu turno ya quedó guardado en el sistema de {catalog.business.name}. La coordinacion final sigue por WhatsApp manual.</p>
              </div>
              <div className="rounded-[2rem] border border-amber-500/15 bg-black/35 p-5">
                <p className="text-sm text-zinc-500">Servicio</p>
                <p className="mt-1 text-2xl font-semibold">{selectedService.name}</p>
                <p className="mt-4 text-sm text-zinc-500">Fecha y hora</p>
                <p className="mt-1 text-lg font-semibold">{formatLongDate(confirmedBooking.start_datetime)}</p>
                <p className="mt-4 text-sm text-zinc-500">Barbero</p>
                <p className="mt-1 text-lg font-semibold">{selectedStaff.name}</p>
              </div>
            </div>
            <div className="space-y-4 rounded-[2rem] border border-zinc-800 bg-black/25 p-6">
              <div className="flex items-center gap-4">
                <Avatar className="h-16 w-16 border border-amber-500/20">
                  <AvatarImage src={selectedStaff.avatar_url || undefined} alt={selectedStaff.name} />
                  <AvatarFallback className="bg-zinc-800 text-zinc-200">{initialsFromName(selectedStaff.name)}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="text-sm text-zinc-500">Reserva a nombre de</p>
                  <p className="font-semibold">{confirmedBooking.customer_name}</p>
                </div>
              </div>
              <Separator className="bg-zinc-800" />
              <div className="space-y-3 text-sm text-zinc-300">
                {catalog.business.phone ? <a href={`tel:${catalog.business.phone}`} className="flex items-center gap-3 transition hover:text-amber-400"><Phone className="h-4 w-4 text-amber-500" />{catalog.business.phone}</a> : null}
                {catalog.business.address ? <div className="flex items-center gap-3"><MapPin className="h-4 w-4 text-amber-500" />{catalog.business.address}</div> : null}
                {catalog.business.instagram_url ? <a href={catalog.business.instagram_url} target="_blank" rel="noreferrer" className="flex items-center gap-3 transition hover:text-amber-400"><Instagram className="h-4 w-4 text-amber-500" />Instagram de Club Amsterdam</a> : null}
              </div>
              <Button onClick={() => window.location.reload()} className="w-full bg-amber-500 font-semibold text-zinc-950 hover:bg-amber-400">Reservar otro turno</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
