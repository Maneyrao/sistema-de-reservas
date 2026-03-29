"use client"

import { useState } from "react"
import { MapPin, Phone, Shield, AlertTriangle } from "lucide-react"

import { cancelAdminBooking, updateAdminBookingStatus } from "@/lib/admin-api"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { humanDateTime, useAdminContext } from "./admin-context"

const STATUS_LABELS: Record<string, string> = {
  confirmed: "Confirmado",
  completed: "Completado",
  no_show: "No se presentó",
}

export function BookingDetailModal() {
  const [confirmCancel, setConfirmCancel] = useState(false)
  const {
    token,
    business,
    selectedBooking,
    setSelectedBooking,
    busyBookingId,
    setBusyBookingId,
    setRescheduleTarget,
    setRescheduleDate,
    setRescheduleTime,
    setRescheduleReason,
    loadSchedule,
    flash,
  } = useAdminContext()

  return (
    <div className="space-y-6">
      <Card className="border-zinc-800 bg-black/30">
        <CardContent className="space-y-4 p-6">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Detalle</p>
            <h3 className="mt-2 font-display text-4xl uppercase leading-none">
              {selectedBooking ? selectedBooking.customer_name : "Seleccioná un turno"}
            </h3>
          </div>
          {selectedBooking ? (
            <>
              <div className="rounded-[1.5rem] border border-zinc-800 bg-black/25 p-4">
                <p className="text-sm text-zinc-500">Servicio</p>
                <p className="mt-2 font-semibold">{selectedBooking.service_name}</p>
                <p className="mt-1 text-sm text-zinc-500">{selectedBooking.staff_name}</p>
              </div>
              <div className="rounded-[1.5rem] border border-zinc-800 bg-black/25 p-4">
                <p className="text-sm text-zinc-500">Fecha</p>
                <p className="mt-2 font-semibold">{humanDateTime(selectedBooking.start_datetime)}</p>
                <p className="mt-2 text-sm text-zinc-500">
                  {selectedBooking.customer_phone || "Sin teléfono"} ·{" "}
                  {selectedBooking.customer_email || "Sin email"}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {(["confirmed", "completed", "no_show"] as const).map((status) => (
                  <button
                    key={status}
                    disabled={busyBookingId === selectedBooking.id}
                    aria-pressed={selectedBooking.status === status}
                    onClick={async () => {
                      if (!token) return
                      setBusyBookingId(selectedBooking.id)
                      try {
                        await updateAdminBookingStatus(token, selectedBooking.id, { status })
                        await loadSchedule(token)
                        flash("success", "Estado actualizado")
                      } catch (error) {
                        flash("error", error instanceof Error ? error.message : "No se pudo actualizar")
                      } finally {
                        setBusyBookingId(null)
                      }
                    }}
                    className={
                      selectedBooking.status === status
                        ? "rounded-full border border-amber-500 bg-amber-500/10 px-3 py-1 text-xs uppercase tracking-[0.16em] text-amber-300"
                        : "rounded-full border border-zinc-700 px-3 py-1 text-xs uppercase tracking-[0.16em] text-zinc-400 hover:border-zinc-500 hover:text-zinc-200 transition-colors"
                    }
                  >
                    {STATUS_LABELS[status]}
                  </button>
                ))}
                <button
                  onClick={() => {
                    setRescheduleTarget(selectedBooking)
                    setRescheduleDate(selectedBooking.start_datetime.slice(0, 10))
                    setRescheduleTime(selectedBooking.start_datetime.slice(11, 16))
                    setRescheduleReason("")
                  }}
                  className="rounded-full border border-zinc-700 px-3 py-1 text-xs uppercase tracking-[0.16em] text-zinc-400 hover:border-zinc-500 hover:text-zinc-200 transition-colors"
                >
                  Mover
                </button>
                {!confirmCancel ? (
                  <button
                    onClick={() => setConfirmCancel(true)}
                    className="rounded-full border border-red-500/40 px-3 py-1 text-xs uppercase tracking-[0.16em] text-red-300 hover:border-red-500/70 transition-colors"
                  >
                    Cancelar turno
                  </button>
                ) : (
                  <div className="w-full mt-2 rounded-2xl border border-red-500/30 bg-red-500/5 p-3 animate-in fade-in duration-200">
                    <div className="flex items-start gap-2 mb-3">
                      <AlertTriangle className="h-4 w-4 shrink-0 text-red-400 mt-0.5" />
                      <p className="text-xs text-red-200 leading-5">
                        ¿Cancelar el turno de <span className="font-semibold">{selectedBooking.customer_name}</span>?
                        Esta acción no se puede deshacer.
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        disabled={busyBookingId === selectedBooking.id}
                        onClick={async () => {
                          if (!token) return
                          setBusyBookingId(selectedBooking.id)
                          try {
                            await cancelAdminBooking(token, selectedBooking.id, "cancelado desde dashboard")
                            await loadSchedule(token)
                            setSelectedBooking(null)
                            setConfirmCancel(false)
                            flash("success", "Turno cancelado")
                          } catch (error) {
                            flash("error", error instanceof Error ? error.message : "No se pudo cancelar")
                          } finally {
                            setBusyBookingId(null)
                          }
                        }}
                        className="bg-red-500 text-white hover:bg-red-400 text-xs px-3 py-1 h-auto rounded-xl"
                      >
                        Sí, cancelar
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setConfirmCancel(false)}
                        className="border-zinc-700 bg-transparent text-zinc-300 text-xs px-3 py-1 h-auto rounded-xl"
                      >
                        No, volver
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <p className="text-sm leading-6 text-zinc-500">
              Elegí un bloque del calendario para ver datos del cliente y actuar sobre el turno.
            </p>
          )}
        </CardContent>
      </Card>
      <Card className="border-zinc-800 bg-black/30">
        <CardContent className="space-y-4 p-6">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Negocio</p>
            <h3 className="mt-2 font-display text-4xl uppercase leading-none">Contacto</h3>
          </div>
          <div className="space-y-3 text-sm text-zinc-300">
            {business?.address ? (
              <div className="flex items-center gap-3">
                <MapPin className="h-4 w-4 text-amber-500" />
                {business.address}
              </div>
            ) : null}
            {business?.phone ? (
              <div className="flex items-center gap-3">
                <Phone className="h-4 w-4 text-amber-500" />
                {business.phone}
              </div>
            ) : null}
            <div className="flex items-center gap-3">
              <Shield className="h-4 w-4 text-amber-500" />
              Matias Damonte
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
