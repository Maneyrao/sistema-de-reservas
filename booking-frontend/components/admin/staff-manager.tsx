"use client"

import { createAdminStaff, deleteAdminStaff, listAdminStaff, updateAdminStaff } from "@/lib/admin-api"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  DAY_OPTIONS,
  emptyStaffForm,
  initialsFromName,
  normalizeSlug,
  useAdminContext,
} from "./admin-context"

export function StaffManager() {
  const {
    token,
    staff,
    setStaff,
    activeServices,
    staffForm,
    setStaffForm,
    editingStaffId,
    setEditingStaffId,
    loadSchedule,
    flash,
  } = useAdminContext()

  async function saveStaff(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) return
    const payload = {
      name: staffForm.name.trim(),
      slug: normalizeSlug(staffForm.slug || staffForm.name),
      title: staffForm.title.trim() || null,
      bio: staffForm.bio.trim() || null,
      avatar_url: staffForm.avatar_url.trim() || null,
      active: staffForm.active,
      service_ids: staffForm.service_ids,
      availability_rules: staffForm.availability_rules.map((item) => ({
        weekday: item.weekday,
        start_time: item.start_time,
        end_time: item.end_time,
      })),
    }
    try {
      if (editingStaffId) await updateAdminStaff(token, editingStaffId, payload)
      else await createAdminStaff(token, payload)
      setEditingStaffId(null)
      setStaffForm(emptyStaffForm())
      setStaff(await listAdminStaff(token))
      await loadSchedule(token)
      flash("success", "Barbero guardado")
    } catch (error) {
      flash("error", error instanceof Error ? error.message : "No se pudo guardar el barbero")
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.95fr,1.05fr]">
      <Card className="border-amber-500/10 bg-zinc-900/85">
        <CardContent className="space-y-4 p-6">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-amber-500/70">Barberos</p>
            <h2 className="mt-2 font-display text-5xl uppercase leading-none">
              {editingStaffId ? "Editar" : "Agregar"}
            </h2>
          </div>
          <form className="grid gap-4" onSubmit={saveStaff}>
            <input
              value={staffForm.name}
              onChange={(event) =>
                setStaffForm((current) => ({
                  ...current,
                  name: event.target.value,
                  slug: current.slug || normalizeSlug(event.target.value),
                }))
              }
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="Nombre"
            />
            <input
              value={staffForm.slug}
              onChange={(event) =>
                setStaffForm((current) => ({ ...current, slug: normalizeSlug(event.target.value) }))
              }
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="slug"
            />
            <input
              value={staffForm.title}
              onChange={(event) => setStaffForm((current) => ({ ...current, title: event.target.value }))}
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="Rol / título"
            />
            <input
              value={staffForm.avatar_url}
              onChange={(event) => setStaffForm((current) => ({ ...current, avatar_url: event.target.value }))}
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="URL de foto"
            />
            <textarea
              value={staffForm.bio}
              onChange={(event) => setStaffForm((current) => ({ ...current, bio: event.target.value }))}
              className="min-h-24 rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="Bio corta"
            />

            <div className="rounded-[1.5rem] border border-zinc-800 bg-black/20 p-4">
              <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">Servicios asignados</p>
              <div className="mt-3 grid gap-2">
                {activeServices.map((service) => (
                  <label
                    key={service.id}
                    className="flex items-center justify-between rounded-xl border border-zinc-800 px-3 py-2 text-sm"
                  >
                    <span>{service.name}</span>
                    <input
                      type="checkbox"
                      checked={staffForm.service_ids.includes(service.id)}
                      onChange={() =>
                        setStaffForm((current) => ({
                          ...current,
                          service_ids: current.service_ids.includes(service.id)
                            ? current.service_ids.filter((item) => item !== service.id)
                            : [...current.service_ids, service.id],
                        }))
                      }
                    />
                  </label>
                ))}
              </div>
            </div>

            <div className="rounded-[1.5rem] border border-zinc-800 bg-black/20 p-4">
              <div className="flex items-center justify-between">
                <p className="text-sm uppercase tracking-[0.2em] text-zinc-500">Disponibilidad semanal</p>
                <button
                  type="button"
                  onClick={() =>
                    setStaffForm((current) => ({
                      ...current,
                      availability_rules: [
                        ...current.availability_rules,
                        { weekday: 0, start_time: "13:45:00", end_time: "20:00:00" },
                      ],
                    }))
                  }
                  className="text-xs uppercase tracking-[0.16em] text-amber-400"
                >
                  Agregar franja
                </button>
              </div>
              <div className="mt-3 grid gap-3">
                {staffForm.availability_rules.map((rule, index) => (
                  <div key={`${rule.weekday}-${index}`} className="grid gap-2 sm:grid-cols-[1fr,1fr,1fr,auto]">
                    <select
                      value={rule.weekday}
                      onChange={(event) =>
                        setStaffForm((current) => ({
                          ...current,
                          availability_rules: current.availability_rules.map((item, itemIndex) =>
                            itemIndex === index ? { ...item, weekday: Number(event.target.value) } : item,
                          ),
                        }))
                      }
                      className="rounded-xl border border-zinc-800 bg-zinc-900/80 px-3 py-2"
                    >
                      {DAY_OPTIONS.map((day) => (
                        <option key={day.value} value={day.value}>
                          {day.label}
                        </option>
                      ))}
                    </select>
                    <input
                      value={rule.start_time}
                      onChange={(event) =>
                        setStaffForm((current) => ({
                          ...current,
                          availability_rules: current.availability_rules.map((item, itemIndex) =>
                            itemIndex === index ? { ...item, start_time: event.target.value } : item,
                          ),
                        }))
                      }
                      className="rounded-xl border border-zinc-800 bg-zinc-900/80 px-3 py-2"
                      type="time"
                      step="900"
                    />
                    <input
                      value={rule.end_time}
                      onChange={(event) =>
                        setStaffForm((current) => ({
                          ...current,
                          availability_rules: current.availability_rules.map((item, itemIndex) =>
                            itemIndex === index ? { ...item, end_time: event.target.value } : item,
                          ),
                        }))
                      }
                      className="rounded-xl border border-zinc-800 bg-zinc-900/80 px-3 py-2"
                      type="time"
                      step="900"
                    />
                    <button
                      type="button"
                      onClick={() =>
                        setStaffForm((current) => ({
                          ...current,
                          availability_rules: current.availability_rules.filter(
                            (_, itemIndex) => itemIndex !== index,
                          ),
                        }))
                      }
                      className="rounded-xl border border-red-500/40 px-3 py-2 text-xs uppercase tracking-[0.16em] text-red-200"
                    >
                      Quitar
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex gap-3">
              <Button type="submit" className="bg-amber-500 text-zinc-950 hover:bg-amber-400">
                {editingStaffId ? "Guardar cambios" : "Crear barbero"}
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setEditingStaffId(null)
                  setStaffForm(emptyStaffForm())
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
          {staff.map((item) => (
            <div key={item.id} className="rounded-[1.5rem] border border-zinc-800 bg-zinc-900/70 p-4">
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <Avatar className="h-14 w-14 border border-amber-500/15">
                    <AvatarImage src={item.avatar_url || undefined} alt={item.name} />
                    <AvatarFallback className="bg-zinc-800 text-zinc-100">
                      {initialsFromName(item.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <p className="text-xl font-semibold">{item.name}</p>
                    <p className="text-sm text-amber-400">{item.title || item.slug}</p>
                  </div>
                </div>
                <Badge className={item.active ? "bg-emerald-500/15 text-emerald-300" : "bg-zinc-700 text-zinc-200"}>
                  {item.active ? "activo" : "inactivo"}
                </Badge>
              </div>
              {item.bio ? <p className="mt-4 text-sm leading-6 text-zinc-400">{item.bio}</p> : null}
              <div className="mt-4 flex flex-wrap gap-2">
                {item.services.map((service) => (
                  <Badge key={service.id} className="bg-amber-500/12 text-amber-300">
                    {service.name}
                  </Badge>
                ))}
              </div>
              <div className="mt-4 grid gap-2">
                {item.availability_rules.map((rule) => (
                  <div key={rule.id} className="text-sm text-zinc-400">
                    {DAY_OPTIONS.find((day) => day.value === rule.weekday)?.label}: {rule.start_time.slice(0, 5)} a{" "}
                    {rule.end_time.slice(0, 5)}
                  </div>
                ))}
              </div>
              <div className="mt-4 flex gap-2">
                <button
                  onClick={() => {
                    setEditingStaffId(item.id)
                    setStaffForm({
                      name: item.name,
                      slug: item.slug,
                      title: item.title || "",
                      bio: item.bio || "",
                      avatar_url: item.avatar_url || "",
                      active: item.active,
                      service_ids: item.services.map((service) => service.id),
                      availability_rules: item.availability_rules.map((rule) => ({
                        weekday: rule.weekday,
                        start_time: rule.start_time,
                        end_time: rule.end_time,
                      })),
                    })
                  }}
                  className="rounded-full border border-zinc-700 px-3 py-1 text-xs uppercase tracking-[0.16em]"
                >
                  Editar
                </button>
                <button
                  onClick={async () => {
                    if (!token || !window.confirm(`Desactivar ${item.name}?`)) return
                    await deleteAdminStaff(token, item.id)
                    setStaff(await listAdminStaff(token))
                    await loadSchedule(token)
                    flash("success", "Barbero desactivado")
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
