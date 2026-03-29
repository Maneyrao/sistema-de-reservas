"use client"

import { listAdminServices, createAdminService, updateAdminService, deleteAdminService } from "@/lib/admin-api"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { emptyServiceForm, formatCurrency, normalizeSlug, useAdminContext } from "./admin-context"

export function ServiceManager() {
  const {
    token,
    services,
    setServices,
    serviceForm,
    setServiceForm,
    editingServiceId,
    setEditingServiceId,
    flash,
  } = useAdminContext()

  async function saveService(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) return
    const payload = {
      name: serviceForm.name.trim(),
      slug: normalizeSlug(serviceForm.slug || serviceForm.name),
      duration_minutes: Number(serviceForm.duration_minutes),
      price_amount: Number(serviceForm.price_amount),
      price_currency: serviceForm.price_currency.trim().toUpperCase(),
      active: serviceForm.active,
    }
    try {
      if (editingServiceId) await updateAdminService(token, editingServiceId, payload)
      else await createAdminService(token, payload)
      setEditingServiceId(null)
      setServiceForm(emptyServiceForm())
      setServices(await listAdminServices(token))
      flash("success", "Servicio guardado")
    } catch (error) {
      flash("error", error instanceof Error ? error.message : "No se pudo guardar el servicio")
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.9fr,1.1fr]">
      <Card className="border-amber-500/10 bg-zinc-900/85">
        <CardContent className="space-y-4 p-6">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-amber-500/70">Servicios</p>
            <h2 className="mt-2 font-display text-5xl uppercase leading-none">
              {editingServiceId ? "Editar" : "Agregar"}
            </h2>
          </div>
          <form className="grid gap-3" onSubmit={saveService}>
            <input
              value={serviceForm.name}
              onChange={(event) =>
                setServiceForm((current) => ({
                  ...current,
                  name: event.target.value,
                  slug: current.slug || normalizeSlug(event.target.value),
                }))
              }
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="Nombre"
            />
            <input
              value={serviceForm.slug}
              onChange={(event) =>
                setServiceForm((current) => ({ ...current, slug: normalizeSlug(event.target.value) }))
              }
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="slug"
            />
            <div className="grid gap-3 sm:grid-cols-3">
              <input
                value={serviceForm.duration_minutes}
                onChange={(event) =>
                  setServiceForm((current) => ({ ...current, duration_minutes: event.target.value }))
                }
                className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
                placeholder="Duración"
              />
              <input
                value={serviceForm.price_amount}
                onChange={(event) =>
                  setServiceForm((current) => ({ ...current, price_amount: event.target.value }))
                }
                className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
                placeholder="Precio"
              />
              <input
                value={serviceForm.price_currency}
                onChange={(event) =>
                  setServiceForm((current) => ({
                    ...current,
                    price_currency: event.target.value.toUpperCase(),
                  }))
                }
                className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
                placeholder="Moneda"
              />
            </div>
            <div className="flex gap-3">
              <Button type="submit" className="bg-amber-500 text-zinc-950 hover:bg-amber-400">
                {editingServiceId ? "Guardar cambios" : "Crear servicio"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setEditingServiceId(null)
                  setServiceForm(emptyServiceForm())
                }}
                className="border-zinc-700 bg-transparent text-zinc-300"
              >
                Limpiar
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-black/30">
        <CardContent className="space-y-4 p-6">
          {services.map((service) => (
            <div key={service.id} className="rounded-[1.5rem] border border-zinc-800 bg-zinc-900/70 p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xl font-semibold">{service.name}</p>
                  <p className="mt-1 text-sm text-zinc-500">{service.slug}</p>
                </div>
                <Badge className={service.active ? "bg-emerald-500/15 text-emerald-300" : "bg-zinc-700 text-zinc-200"}>
                  {service.active ? "activo" : "inactivo"}
                </Badge>
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-zinc-300">
                <span>{service.duration_minutes} min</span>
                <span>{formatCurrency(service.price_amount, service.price_currency)}</span>
              </div>
              <div className="mt-4 flex gap-2">
                <button
                  onClick={() => {
                    setEditingServiceId(service.id)
                    setServiceForm({
                      name: service.name,
                      slug: service.slug,
                      duration_minutes: String(service.duration_minutes),
                      price_amount: String(service.price_amount),
                      price_currency: service.price_currency,
                      active: service.active,
                    })
                  }}
                  className="rounded-full border border-zinc-700 px-3 py-1 text-xs uppercase tracking-[0.16em]"
                >
                  Editar
                </button>
                <button
                  onClick={async () => {
                    if (!token || !window.confirm(`Desactivar ${service.name}?`)) return
                    await deleteAdminService(token, service.id)
                    setServices(await listAdminServices(token))
                    flash("success", "Servicio desactivado")
                  }}
                  className="rounded-full border border-red-500/40 px-3 py-1 text-xs uppercase tracking-[0.16em] text-red-200"
                >
                  Desactivar
                </button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
