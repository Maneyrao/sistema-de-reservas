"use client"

import { ChevronLeft, ChevronRight } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import {
  addDays,
  humanDateTime,
  humanDayLabel,
  startOfWeek,
  statusClass,
  timeToMinutes,
  useAdminContext,
} from "./admin-context"
import { BookingDetailModal } from "./booking-detail-modal"

export function AgendaView() {
  const { bookings, weekDays, weekStart, setWeekStart, setSelectedBooking, setShowCreateBooking, staff } =
    useAdminContext()

  const earliestMinutes = Math.min(
    ...staff.flatMap((item) =>
      item.availability_rules.map((rule) => Math.floor(timeToMinutes(rule.start_time) / 60) * 60),
    ),
    12 * 60,
  )
  const latestMinutes = Math.max(
    ...staff.flatMap((item) =>
      item.availability_rules.map((rule) => Math.ceil(timeToMinutes(rule.end_time) / 60) * 60),
    ),
    21 * 60,
  )
  const pixelsPerMinute = 1.05
  const calendarHeight = Math.max((latestMinutes - earliestMinutes) * pixelsPerMinute, 420)

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

          <div className="rounded-[2rem] border border-zinc-800 bg-black/20 p-4">
            {/* Desktop calendar grid */}
            <div className="hidden xl:grid xl:grid-cols-[64px_repeat(7,minmax(0,1fr))] xl:gap-3">
              <div></div>
              {weekDays.map((day) => (
                <div key={day} className="rounded-2xl border border-zinc-800 bg-black/30 p-3 text-center">
                  <p className="text-sm font-semibold">{humanDayLabel(day)}</p>
                </div>
              ))}

              {/* Time labels column */}
              <div className="relative" style={{ height: `${calendarHeight}px` }}>
                {Array.from(
                  { length: Math.floor((latestMinutes - earliestMinutes) / 60) + 1 },
                  (_, index) => earliestMinutes + index * 60,
                ).map((minute) => (
                  <div
                    key={minute}
                    className="absolute left-0 text-xs text-zinc-500"
                    style={{ top: `${(minute - earliestMinutes) * pixelsPerMinute - 8}px` }}
                  >
                    {`${String(Math.floor(minute / 60)).padStart(2, "0")}:00`}
                  </div>
                ))}
              </div>

              {/* Day columns */}
              {weekDays.map((day) => (
                <div
                  key={day}
                  className="relative overflow-hidden rounded-[1.5rem] border border-zinc-800 bg-zinc-950/70"
                  style={{ height: `${calendarHeight}px` }}
                >
                  {/* Hour grid lines */}
                  {Array.from(
                    { length: Math.floor((latestMinutes - earliestMinutes) / 60) + 1 },
                    (_, index) => earliestMinutes + index * 60,
                  ).map((minute) => (
                    <div
                      key={minute}
                      className="absolute inset-x-0 border-t border-zinc-800/70"
                      style={{ top: `${(minute - earliestMinutes) * pixelsPerMinute}px` }}
                    />
                  ))}

                  {/* Bookings */}
                  {bookings
                    .filter((item) => item.start_datetime.slice(0, 10) === day)
                    .map((booking) => {
                      const startMinutes = timeToMinutes(booking.start_datetime.slice(11, 16))
                      const endMinutes = timeToMinutes(booking.end_datetime.slice(11, 16))
                      return (
                        <button
                          key={booking.id}
                          onClick={() => setSelectedBooking(booking)}
                          className={cn(
                            "absolute inset-x-2 rounded-2xl border p-2 text-left",
                            booking.status === "completed"
                              ? "border-emerald-500/35 bg-emerald-500/15"
                              : booking.status === "canceled"
                                ? "border-red-500/35 bg-red-500/15"
                                : booking.status === "no_show"
                                  ? "border-zinc-600 bg-zinc-700/60"
                                  : "border-amber-500/30 bg-amber-500/15",
                          )}
                          style={{
                            top: `${(startMinutes - earliestMinutes) * pixelsPerMinute}px`,
                            height: `${Math.max((endMinutes - startMinutes) * pixelsPerMinute, 56)}px`,
                          }}
                        >
                          <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-300">
                            {booking.start_datetime.slice(11, 16)}
                          </p>
                          <p className="mt-1 text-sm font-semibold">{booking.customer_name}</p>
                          <p className="mt-1 text-xs text-zinc-300">{booking.service_name}</p>
                        </button>
                      )
                    })}
                </div>
              ))}
            </div>

            {/* Mobile list */}
            <div className="mt-4 grid gap-3 xl:hidden">
              {weekDays.map((day) => (
                <div key={day} className="rounded-[1.5rem] border border-zinc-800 bg-black/25 p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <p className="text-sm font-semibold">{humanDayLabel(day)}</p>
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
          </div>
        </CardContent>
      </Card>
      <BookingDetailModal />
    </div>
  )
}
