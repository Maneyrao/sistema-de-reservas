"use client"

import { createAdminBooking } from "@/lib/admin-api"
import { Button } from "@/components/ui/button"
import { emptyBookingForm, formatCurrency, useAdminContext } from "./admin-context"

export function CreateBookingModal() {
  const {
    token,
    activeStaff,
    staff,
    showCreateBooking,
    setShowCreateBooking,
    bookingForm,
    setBookingForm,
    loadSchedule,
    flash,
  } = useAdminContext()

  if (!showCreateBooking) return null

  const manualServices =
    staff.find((item) => item.slug === bookingForm.staff_slug)?.services.filter((item) => item.active) ?? []

  async function submitManualBooking(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) return
    try {
      await createAdminBooking(token, {
        staff_slug: bookingForm.staff_slug,
        service_slug: bookingForm.service_slug,
        date: bookingForm.date,
        time: `${bookingForm.time}:00`,
        customer: {
          first_name: bookingForm.first_name,
          last_name: bookingForm.last_name,
          phone: bookingForm.phone,
          ...(bookingForm.email ? { email: bookingForm.email } : {}),
        },
        notes: bookingForm.notes || null,
        status: bookingForm.status,
      })
      setShowCreateBooking(false)
      setBookingForm(emptyBookingForm(activeStaff[0]?.slug || ""))
      await loadSchedule(token)
      flash("success", "Turno creado")
    } catch (error) {
      flash("error", error instanceof Error ? error.message : "No se pudo crear el turno")
    }
  }

  const selectedService = manualServices.find((item) => item.slug === bookingForm.service_slug)

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 px-4">
      <form
        onSubmit={submitManualBooking}
        className="w-full max-w-2xl rounded-[2rem] border border-amber-500/15 bg-zinc-900 p-6"
      >
        <div>
          <p className="text-xs uppercase tracking-[0.35em] text-amber-500/70">Alta manual</p>
          <h3 className="mt-2 font-display text-5xl uppercase leading-none">Nuevo turno</h3>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          <select
            value={bookingForm.staff_slug}
            onChange={(event) => setBookingForm((current) => ({ ...current, staff_slug: event.target.value }))}
            className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
          >
            {activeStaff.map((item) => (
              <option key={item.id} value={item.slug}>
                {item.name}
              </option>
            ))}
          </select>
          <select
            value={bookingForm.service_slug}
            onChange={(event) => setBookingForm((current) => ({ ...current, service_slug: event.target.value }))}
            className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
          >
            {manualServices.map((item) => (
              <option key={item.id} value={item.slug}>
                {item.name}
              </option>
            ))}
          </select>
          <input
            type="date"
            value={bookingForm.date}
            onChange={(event) => setBookingForm((current) => ({ ...current, date: event.target.value }))}
            className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
          />
          <input
            type="time"
            value={bookingForm.time}
            onChange={(event) => setBookingForm((current) => ({ ...current, time: event.target.value }))}
            className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
          />
          <input
            value={bookingForm.first_name}
            onChange={(event) => setBookingForm((current) => ({ ...current, first_name: event.target.value }))}
            className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
            placeholder="Nombre"
          />
          <input
            value={bookingForm.last_name}
            onChange={(event) => setBookingForm((current) => ({ ...current, last_name: event.target.value }))}
            className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
            placeholder="Apellido"
          />
          <input
            value={bookingForm.phone}
            onChange={(event) => setBookingForm((current) => ({ ...current, phone: event.target.value }))}
            className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
            placeholder="Teléfono"
          />
          <input
            value={bookingForm.email}
            onChange={(event) => setBookingForm((current) => ({ ...current, email: event.target.value }))}
            className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
            placeholder="Email opcional"
          />
          <select
            value={bookingForm.status}
            onChange={(event) => setBookingForm((current) => ({ ...current, status: event.target.value }))}
            className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
          >
            <option value="confirmed">Confirmado</option>
            <option value="pending">Pendiente</option>
          </select>
          <input
            value={selectedService ? formatCurrency(selectedService.price_amount, selectedService.price_currency) : ""}
            className="rounded-2xl border border-zinc-800 bg-black/15 px-4 py-3 text-zinc-400"
            disabled
            placeholder="Precio"
          />
        </div>
        <textarea
          value={bookingForm.notes}
          onChange={(event) => setBookingForm((current) => ({ ...current, notes: event.target.value }))}
          className="mt-3 min-h-24 w-full rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
          placeholder="Notas del turno"
        />
        <div className="mt-5 flex gap-3">
          <Button type="submit" className="bg-amber-500 text-zinc-950 hover:bg-amber-400">
            Crear turno
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => setShowCreateBooking(false)}
            className="border-zinc-700 bg-transparent text-zinc-300"
          >
            Cerrar
          </Button>
        </div>
      </form>
    </div>
  )
}
