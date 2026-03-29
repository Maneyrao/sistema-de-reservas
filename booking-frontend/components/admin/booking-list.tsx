"use client"

import { ChevronLeft, ChevronRight } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { addDays, humanDateTime, startOfWeek, statusClass, useAdminContext } from "./admin-context"
import { BookingDetailModal } from "./booking-detail-modal"

export function BookingList() {
  const { bookings, weekDays, weekStart, setWeekStart, setSelectedBooking, setShowCreateBooking } = useAdminContext()

  return (
    <div className="grid gap-6 xl:grid-cols-[1.3fr,0.7fr]">
      <Card className="border-amber-500/10 bg-zinc-900/85">
        <CardContent className="space-y-5 p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-amber-500/70">Agenda semanal</p>
              <h2 className="mt-2 font-display text-5xl uppercase leading-none">Calendario visual</h2>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button
                variant="outline"
                onClick={() => setWeekStart(addDays(weekStart, -7))}
                className="border-zinc-700 bg-transparent text-zinc-300"
              >
                <ChevronLeft className="mr-2 h-4 w-4" />
                Semana anterior
              </Button>
              <Button
                variant="outline"
                onClick={() => setWeekStart(startOfWeek())}
                className="border-zinc-700 bg-transparent text-zinc-300"
              >
                Hoy
              </Button>
              <Button
                variant="outline"
                onClick={() => setWeekStart(addDays(weekStart, 7))}
                className="border-zinc-700 bg-transparent text-zinc-300"
              >
                Siguiente
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
              <Button
                onClick={() => setShowCreateBooking(true)}
                className="bg-amber-500 text-zinc-950 hover:bg-amber-400"
              >
                Nuevo turno
              </Button>
            </div>
          </div>

          {/* Mobile list */}
          <div className="mt-4 grid gap-3 xl:hidden">
            {weekDays.map((day) => (
              <div key={day} className="rounded-[1.5rem] border border-zinc-800 bg-black/25 p-4">
                <div className="mb-3 flex items-center justify-between">
                  <p className="text-sm font-semibold">
                    {new Date(`${day}T00:00:00`).toLocaleDateString("es-AR", {
                      weekday: "short",
                      day: "numeric",
                      month: "short",
                    })}
                  </p>
                  <Badge className="bg-zinc-800 text-zinc-300">
                    {bookings.filter((item) => item.start_datetime.slice(0, 10) === day).length} turnos
                  </Badge>
                </div>
                <div className="space-y-3">
                  {bookings
                    .filter((item) => item.start_datetime.slice(0, 10) === day)
                    .map((booking) => (
                      <button
                        key={booking.id}
                        onClick={() => setSelectedBooking(booking)}
                        className="w-full rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4 text-left"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-semibold">{booking.customer_name}</p>
                            <p className="mt-1 text-sm text-zinc-500">{booking.service_name}</p>
                          </div>
                          <Badge className={cn("rounded-full px-3 py-1", statusClass(booking.status))}>
                            {booking.status}
                          </Badge>
                        </div>
                        <p className="mt-3 text-sm text-zinc-300">{humanDateTime(booking.start_datetime)}</p>
                      </button>
                    ))}
                  {bookings.filter((item) => item.start_datetime.slice(0, 10) === day).length === 0 ? (
                    <p className="text-sm text-zinc-500">Sin turnos.</p>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      <BookingDetailModal />
    </div>
  )
}
