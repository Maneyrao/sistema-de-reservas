"use client"

import { useBooking } from "@/components/booking/booking-context"
import { inputClasses } from "@/components/booking/utils"
import { cn } from "@/lib/utils"

export function CustomerForm() {
  const { customer, setCustomer, submitError } = useBooking()

  return (
    <div className="space-y-5">
      <div>
        <p className="text-xs uppercase tracking-[0.45em] text-amber-500/70">Paso 3</p>
        <h2 className="mt-2 font-display text-5xl uppercase leading-none">Completá tus datos</h2>
        <p className="mt-3 max-w-2xl text-sm text-zinc-400">Solo pedimos lo necesario para registrar el turno y contactarte manualmente.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <input
          value={customer.firstName}
          onChange={(event) => setCustomer((value) => ({ ...value, firstName: event.target.value }))}
          className={inputClasses(customer.firstName.trim().length > 0 && customer.firstName.trim().length < 2)}
          placeholder="Nombre"
        />
        <input
          value={customer.lastName}
          onChange={(event) => setCustomer((value) => ({ ...value, lastName: event.target.value }))}
          className={inputClasses(customer.lastName.trim().length > 0 && customer.lastName.trim().length < 2)}
          placeholder="Apellido"
        />
        <input
          value={customer.phone}
          onChange={(event) => setCustomer((value) => ({ ...value, phone: event.target.value }))}
          className={inputClasses(customer.phone.trim().length > 0 && customer.phone.trim().replace(/\D/g, "").length < 8)}
          placeholder="Telefono"
        />
        <input
          value={customer.email}
          onChange={(event) => setCustomer((value) => ({ ...value, email: event.target.value }))}
          className={inputClasses(false)}
          placeholder="Email (opcional)"
        />
      </div>
      <textarea
        value={customer.notes}
        onChange={(event) => setCustomer((value) => ({ ...value, notes: event.target.value }))}
        className={cn(inputClasses(false), "min-h-28 resize-none")}
        placeholder="Notas para el turno (opcional)"
      />
      {submitError ? <p className="text-sm text-red-300">{submitError}</p> : null}
    </div>
  )
}
