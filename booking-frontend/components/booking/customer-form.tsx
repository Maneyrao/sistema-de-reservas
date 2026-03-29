"use client"

import { useBooking } from "@/components/booking/booking-context"
import { inputClasses } from "@/components/booking/utils"
import { cn } from "@/lib/utils"

export function CustomerForm() {
  const { customer, setCustomer, selectedService } = useBooking()

  const firstNameInvalid = customer.firstName.trim().length > 0 && customer.firstName.trim().length < 2
  const lastNameInvalid = customer.lastName.trim().length > 0 && customer.lastName.trim().length < 2
  const phoneInvalid = customer.phone.trim().length > 0 && customer.phone.trim().replace(/\D/g, "").length < 8

  return (
    <div className="space-y-5">
      <div>
        <h2 className="font-display text-3xl uppercase leading-none">Tus datos</h2>
        <p className="mt-1 text-sm text-zinc-400">Solo lo necesario para registrar el turno.</p>
      </div>

      {/* Campos obligatorios */}
      <div className="space-y-3">
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="space-y-1">
            <input
              type="text"
              value={customer.firstName}
              onChange={(e) => setCustomer((v) => ({ ...v, firstName: e.target.value }))}
              className={inputClasses(firstNameInvalid)}
              placeholder="Nombre *"
              autoComplete="given-name"
            />
            {firstNameInvalid && <p className="px-1 text-[11px] text-red-400">Mínimo 2 caracteres</p>}
          </div>
          <div className="space-y-1">
            <input
              type="text"
              value={customer.lastName}
              onChange={(e) => setCustomer((v) => ({ ...v, lastName: e.target.value }))}
              className={inputClasses(lastNameInvalid)}
              placeholder="Apellido *"
              autoComplete="family-name"
            />
            {lastNameInvalid && <p className="px-1 text-[11px] text-red-400">Mínimo 2 caracteres</p>}
          </div>
        </div>

        <div className="space-y-1">
          <input
            type="tel"
            value={customer.phone}
            onChange={(e) => setCustomer((v) => ({ ...v, phone: e.target.value }))}
            className={inputClasses(phoneInvalid)}
            placeholder="WhatsApp / Teléfono * — ej: 11 1234-5678"
            autoComplete="tel"
          />
          {phoneInvalid && <p className="px-1 text-[11px] text-red-400">Ingresá al menos 8 dígitos</p>}
        </div>
      </div>

      {/* Separador opcionales */}
      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-zinc-800" />
        <span className="text-[10px] uppercase tracking-[0.3em] text-zinc-600">Opcionales</span>
        <div className="h-px flex-1 bg-zinc-800" />
      </div>

      <div className="space-y-3">
        <input
          type="email"
          value={customer.email}
          onChange={(e) => setCustomer((v) => ({ ...v, email: e.target.value }))}
          className={inputClasses(false)}
          placeholder="Email"
          autoComplete="email"
        />
        <textarea
          value={customer.notes}
          onChange={(e) => setCustomer((v) => ({ ...v, notes: e.target.value }))}
          className={cn(inputClasses(false), "min-h-24 resize-none")}
          placeholder="Notas para el turno — preferencias, alergias, etc."
        />
      </div>
    </div>
  )
}
