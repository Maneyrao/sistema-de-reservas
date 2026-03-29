"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { useAdminContext } from "./admin-context"

export function LoginForm() {
  const { loginEmail, setLoginEmail, loginPassword, setLoginPassword, loginError, loginLoading, handleLogin } =
    useAdminContext()

  return (
    <div className="min-h-screen bg-zinc-950 px-4 py-10 text-zinc-50">
      <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[1.1fr,0.9fr]">
        <Card className="overflow-hidden border-amber-500/15 bg-zinc-900/90">
          <CardContent className="space-y-6 p-8">
            <div className="flex items-center gap-4">
              <img
                src="/club-amsterdam-monogram.svg"
                alt="Club Amsterdam"
                className="h-20 w-20 rounded-2xl border border-amber-500/15 bg-black/35 p-2"
              />
              <div>
                <p className="text-xs uppercase tracking-[0.45em] text-amber-500/75">Acceso Privado</p>
                <h1 className="font-display text-6xl uppercase leading-none">Admin Club</h1>
              </div>
            </div>
            <p className="max-w-xl text-zinc-400">
              Panel premium para agenda visual, reservas manuales, staff, servicios, bloqueos y contenido público.
            </p>
            <form className="grid gap-4" onSubmit={handleLogin}>
              <input
                value={loginEmail}
                onChange={(event) => setLoginEmail(event.target.value)}
                className="rounded-2xl border border-amber-500/15 bg-black/35 px-4 py-3"
                placeholder="Email"
                type="email"
              />
              <input
                value={loginPassword}
                onChange={(event) => setLoginPassword(event.target.value)}
                className="rounded-2xl border border-amber-500/15 bg-black/35 px-4 py-3"
                placeholder="Contraseña"
                type="password"
              />
              {loginError ? <p className="text-sm text-red-300">{loginError}</p> : null}
              <Button type="submit" disabled={loginLoading} className="bg-amber-500 text-zinc-950 hover:bg-amber-400">
                {loginLoading ? "Ingresando..." : "Ingresar al dashboard"}
              </Button>
            </form>
          </CardContent>
        </Card>
        <Card className="border-zinc-800 bg-black/35">
          <CardContent className="space-y-5 p-8">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-zinc-500">Brand Fit</p>
              <h2 className="mt-2 font-display text-5xl uppercase leading-none">Negro y dorado</h2>
            </div>
            <div className="grid gap-4">
              <div className="rounded-[1.5rem] border border-zinc-800 bg-zinc-900/80 p-4">
                <p className="text-sm text-zinc-500">Agenda</p>
                <p className="mt-2 font-semibold text-zinc-100">Calendario semanal visual y operación rápida</p>
              </div>
              <div className="rounded-[1.5rem] border border-zinc-800 bg-zinc-900/80 p-4">
                <p className="text-sm text-zinc-500">Contenido</p>
                <p className="mt-2 font-semibold text-zinc-100">Marca pública editable y perfiles de barberos</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
