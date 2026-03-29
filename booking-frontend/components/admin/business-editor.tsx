"use client"

import { CalendarDays, MapPin, Phone } from "lucide-react"

import { updateAdminBusiness } from "@/lib/admin-api"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { useAdminContext } from "./admin-context"

export function BusinessEditor() {
  const { token, businessForm, setBusinessForm, setBusiness, flash } = useAdminContext()

  async function saveBusiness(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) return
    try {
      const updated = await updateAdminBusiness(
        token,
        Object.fromEntries(Object.entries(businessForm).map(([key, value]) => [key, value.trim() || null])),
      )
      setBusiness(updated)
      flash("success", "Marca pública actualizada")
    } catch (error) {
      flash("error", error instanceof Error ? error.message : "No se pudo actualizar el negocio")
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.95fr,1.05fr]">
      <Card className="border-amber-500/10 bg-zinc-900/85">
        <CardContent className="space-y-4 p-6">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-amber-500/70">Business</p>
            <h2 className="mt-2 font-display text-5xl uppercase leading-none">Marca pública</h2>
          </div>
          <form className="grid gap-3" onSubmit={saveBusiness}>
            <input
              value={businessForm.name}
              onChange={(event) => setBusinessForm((current) => ({ ...current, name: event.target.value }))}
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="Nombre"
            />
            <input
              value={businessForm.tagline}
              onChange={(event) => setBusinessForm((current) => ({ ...current, tagline: event.target.value }))}
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="Tagline"
            />
            <input
              value={businessForm.hero_title}
              onChange={(event) => setBusinessForm((current) => ({ ...current, hero_title: event.target.value }))}
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="Hero title"
            />
            <textarea
              value={businessForm.hero_description}
              onChange={(event) =>
                setBusinessForm((current) => ({ ...current, hero_description: event.target.value }))
              }
              className="min-h-24 rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="Hero description"
            />
            <input
              value={businessForm.announcement}
              onChange={(event) =>
                setBusinessForm((current) => ({ ...current, announcement: event.target.value }))
              }
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="Aviso destacado"
            />
            <input
              value={businessForm.booking_note}
              onChange={(event) =>
                setBusinessForm((current) => ({ ...current, booking_note: event.target.value }))
              }
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="Nota de reserva"
            />
            <input
              value={businessForm.address}
              onChange={(event) => setBusinessForm((current) => ({ ...current, address: event.target.value }))}
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="Dirección"
            />
            <div className="grid gap-3 sm:grid-cols-2">
              <input
                value={businessForm.phone}
                onChange={(event) => setBusinessForm((current) => ({ ...current, phone: event.target.value }))}
                className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
                placeholder="Teléfono"
              />
              <input
                value={businessForm.instagram_url}
                onChange={(event) =>
                  setBusinessForm((current) => ({ ...current, instagram_url: event.target.value }))
                }
                className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
                placeholder="Instagram URL"
              />
            </div>
            <input
              value={businessForm.maps_url}
              onChange={(event) => setBusinessForm((current) => ({ ...current, maps_url: event.target.value }))}
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="Google Maps URL"
            />
            <Button type="submit" className="bg-amber-500 text-zinc-950 hover:bg-amber-400">
              Guardar marca pública
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-black/30">
        <CardContent className="space-y-4 p-6">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Preview</p>
            <h3 className="mt-2 font-display text-4xl uppercase leading-none">
              {businessForm.name || "Club Amsterdam"}
            </h3>
            <p className="mt-4 text-sm text-zinc-400">
              {businessForm.hero_title || businessForm.tagline || "Experiencia premium en cada corte"}
            </p>
            <p className="mt-3 text-sm leading-6 text-zinc-500">
              {businessForm.hero_description ||
                "La portada pública del sistema se alimenta desde este formulario."}
            </p>
          </div>
          <div className="rounded-[1.5rem] border border-amber-500/15 bg-black/25 p-5">
            <p className="text-xs uppercase tracking-[0.28em] text-zinc-500">Aviso destacado</p>
            <p className="mt-3 text-sm text-zinc-200">
              {businessForm.announcement || "Sin aviso configurado."}
            </p>
          </div>
          <div className="space-y-3 text-sm text-zinc-300">
            {businessForm.address ? (
              <div className="flex items-center gap-3">
                <MapPin className="h-4 w-4 text-amber-500" />
                {businessForm.address}
              </div>
            ) : null}
            {businessForm.phone ? (
              <div className="flex items-center gap-3">
                <Phone className="h-4 w-4 text-amber-500" />
                {businessForm.phone}
              </div>
            ) : null}
            <div className="flex items-center gap-3">
              <CalendarDays className="h-4 w-4 text-amber-500" />
              {businessForm.booking_note || "Sin nota de reserva"}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
