"use client"

import { rescheduleAdminBooking } from "@/lib/admin-api"
import { BrandLoader } from "@/components/brand-loader"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

import { AdminProvider, useAdminContext } from "./admin-context"
import { LoginForm } from "./login-form"
import { Sidebar } from "./sidebar"
import { AgendaView } from "./agenda-view"
import { ServiceManager } from "./service-manager"
import { StaffManager } from "./staff-manager"
import { BusinessEditor } from "./business-editor"
import { BlockManager } from "./block-manager"
import { CreateBookingModal } from "./create-booking-modal"

// ─── Reschedule modal (small, kept here to avoid extra file for a tiny modal) ──

function RescheduleModal() {
  const {
    token,
    rescheduleTarget,
    setRescheduleTarget,
    rescheduleDate,
    setRescheduleDate,
    rescheduleTime,
    setRescheduleTime,
    rescheduleReason,
    setRescheduleReason,
    busyBookingId,
    setBusyBookingId,
    loadSchedule,
    flash,
  } = useAdminContext()

  if (!rescheduleTarget) return null

  async function submitReschedule(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token || !rescheduleTarget) return
    setBusyBookingId(rescheduleTarget.id)
    try {
      await rescheduleAdminBooking(token, rescheduleTarget.id, {
        new_date: rescheduleDate,
        new_time: `${rescheduleTime}:00`,
        reason: rescheduleReason || null,
      })
      setRescheduleTarget(null)
      await loadSchedule(token)
      flash("success", "Turno reprogramado")
    } catch (error) {
      flash("error", error instanceof Error ? error.message : "No se pudo mover el turno")
    } finally {
      setBusyBookingId(null)
    }
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 px-4">
      <form
        onSubmit={submitReschedule}
        className="w-full max-w-xl rounded-[2rem] border border-amber-500/15 bg-zinc-900 p-6"
      >
        <p className="text-xs uppercase tracking-[0.35em] text-amber-500/70">Reprogramar</p>
        <h3 className="mt-2 font-display text-5xl uppercase leading-none">Mover turno</h3>
        <p className="mt-3 text-sm text-zinc-400">
          {rescheduleTarget.customer_name} · {rescheduleTarget.service_name}
        </p>
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <input
            type="date"
            value={rescheduleDate}
            onChange={(event) => setRescheduleDate(event.target.value)}
            className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
          />
          <input
            type="time"
            value={rescheduleTime}
            onChange={(event) => setRescheduleTime(event.target.value)}
            className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
          />
        </div>
        <input
          value={rescheduleReason}
          onChange={(event) => setRescheduleReason(event.target.value)}
          className="mt-3 w-full rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
          placeholder="Motivo (opcional)"
        />
        <div className="mt-5 flex gap-3">
          <Button
            type="submit"
            disabled={busyBookingId === rescheduleTarget.id}
            className="bg-amber-500 text-zinc-950 hover:bg-amber-400"
          >
            Guardar cambio
          </Button>
          <Button
            type="button"
            variant="outline"
            onClick={() => setRescheduleTarget(null)}
            className="border-zinc-700 bg-transparent text-zinc-300"
          >
            Cerrar
          </Button>
        </div>
      </form>
    </div>
  )
}

// ─── Stats strip ──────────────────────────────────────────────────────────────

function StatsStrip() {
  const { bookings, activeStaff, activeServices } = useAdminContext()

  const stats = [
    { label: "Turnos en semana", value: bookings.length },
    { label: "Pendientes", value: bookings.filter((item) => item.status === "pending").length },
    { label: "Barberos activos", value: activeStaff.length },
    { label: "Servicios activos", value: activeServices.length },
  ]

  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {stats.map((item) => (
        <Card key={item.label} className="border-zinc-800 bg-black/30">
          <CardContent className="p-5">
            <p className="text-sm text-zinc-500">{item.label}</p>
            <p className="mt-2 text-3xl font-semibold">{item.value}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// ─── Main dashboard shell (requires AdminProvider) ────────────────────────────

function AdminDashboardShell() {
  const { authReady, isAuthenticated, notice, activeTab, loadingData } = useAdminContext()

  if (!authReady) return <BrandLoader message="Cargando acceso privado..." />
  if (!isAuthenticated) return <LoginForm />

  return (
    <div className="min-h-screen bg-zinc-950 px-4 py-6 text-zinc-50">
      {notice ? (
        <div
          className={cn(
            "fixed right-4 top-4 z-50 rounded-2xl border px-4 py-3 text-sm",
            notice.tone === "success"
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-100"
              : "border-red-500/30 bg-red-500/10 text-red-100",
          )}
        >
          {notice.text}
        </div>
      ) : null}

      <div className="mx-auto max-w-7xl space-y-6">
        <Sidebar />
        <StatsStrip />
        {loadingData ? (
          <BrandLoader fullscreen={false} message="Actualizando dashboard..." className="bg-transparent" />
        ) : null}
        {activeTab === "agenda" ? <AgendaView /> : null}
        {activeTab === "services" ? <ServiceManager /> : null}
        {activeTab === "staff" ? <StaffManager /> : null}
        {activeTab === "business" ? <BusinessEditor /> : null}
        {activeTab === "blocks" ? <BlockManager /> : null}
      </div>

      <CreateBookingModal />
      <RescheduleModal />
    </div>
  )
}

// ─── Public export: AdminDashboard wrapped with AdminProvider ─────────────────

export function AdminDashboard() {
  return (
    <AdminProvider>
      <AdminDashboardShell />
    </AdminProvider>
  )
}
