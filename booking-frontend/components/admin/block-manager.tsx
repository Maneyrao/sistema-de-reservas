"use client"

import { createAdminBlock, deleteAdminBlock, listAdminBlocks } from "@/lib/admin-api"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { emptyBlockForm, humanDateTime, useAdminContext } from "./admin-context"

export function BlockManager() {
  const {
    token,
    blocks,
    setBlocks,
    activeStaff,
    blockForm,
    setBlockForm,
    weekStart,
    weekEnd,
    flash,
  } = useAdminContext()

  async function saveBlock(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) return
    try {
      await createAdminBlock(token, {
        staff_slug: blockForm.staff_slug || null,
        start_datetime: new Date(blockForm.start_datetime).toISOString(),
        end_datetime: new Date(blockForm.end_datetime).toISOString(),
        reason: blockForm.reason || null,
        notes: blockForm.notes || null,
      })
      setBlockForm(emptyBlockForm(activeStaff[0]?.slug || ""))
      setBlocks(await listAdminBlocks(token, { dateFrom: weekStart, dateTo: weekEnd }))
      flash("success", "Bloqueo creado")
    } catch (error) {
      flash("error", error instanceof Error ? error.message : "No se pudo crear el bloqueo")
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[0.9fr,1.1fr]">
      <Card className="border-amber-500/10 bg-zinc-900/85">
        <CardContent className="space-y-4 p-6">
          <div>
            <p className="text-xs uppercase tracking-[0.35em] text-amber-500/70">Bloqueos</p>
            <h2 className="mt-2 font-display text-5xl uppercase leading-none">Agenda cerrada</h2>
          </div>
          <form className="grid gap-3" onSubmit={saveBlock}>
            <select
              value={blockForm.staff_slug}
              onChange={(event) => setBlockForm((current) => ({ ...current, staff_slug: event.target.value }))}
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
            >
              <option value="">Bloqueo global</option>
              {activeStaff.map((item) => (
                <option key={item.id} value={item.slug}>
                  {item.name}
                </option>
              ))}
            </select>
            <input
              type="datetime-local"
              value={blockForm.start_datetime}
              onChange={(event) => setBlockForm((current) => ({ ...current, start_datetime: event.target.value }))}
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
            />
            <input
              type="datetime-local"
              value={blockForm.end_datetime}
              onChange={(event) => setBlockForm((current) => ({ ...current, end_datetime: event.target.value }))}
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
            />
            <input
              value={blockForm.reason}
              onChange={(event) => setBlockForm((current) => ({ ...current, reason: event.target.value }))}
              className="rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="Motivo"
            />
            <textarea
              value={blockForm.notes}
              onChange={(event) => setBlockForm((current) => ({ ...current, notes: event.target.value }))}
              className="min-h-28 rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3"
              placeholder="Notas"
            />
            <Button type="submit" className="bg-amber-500 text-zinc-950 hover:bg-amber-400">
              Crear bloqueo
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-black/30">
        <CardContent className="space-y-4 p-6">
          {blocks.length === 0 ? (
            <p className="text-sm text-zinc-400">No hay bloqueos para la semana elegida.</p>
          ) : (
            blocks.map((block) => (
              <div key={block.id} className="rounded-[1.5rem] border border-zinc-800 bg-zinc-900/70 p-4">
                <p className="font-semibold">
                  {humanDateTime(block.start_datetime)} → {humanDateTime(block.end_datetime)}
                </p>
                <p className="mt-2 text-sm text-zinc-500">
                  Staff: {block.staff_slug || "global"} · Motivo: {block.reason || "-"}
                </p>
                {block.notes ? <p className="mt-2 text-sm text-zinc-400">{block.notes}</p> : null}
                <div className="mt-4">
                  <button
                    onClick={async () => {
                      if (!token || !window.confirm("Eliminar bloqueo?")) return
                      await deleteAdminBlock(token, block.id)
                      setBlocks(await listAdminBlocks(token, { dateFrom: weekStart, dateTo: weekEnd }))
                      flash("success", "Bloqueo eliminado")
                    }}
                    className="rounded-full border border-red-500/40 px-3 py-1 text-xs uppercase tracking-[0.16em] text-red-200"
                  >
                    Eliminar
                  </button>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  )
}
