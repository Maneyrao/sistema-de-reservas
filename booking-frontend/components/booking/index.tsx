"use client"

import { useEffect, useRef, useState } from "react"
import { AlertCircle, ChevronLeft, ChevronRight, Clock3, Instagram, MapPin, Phone } from "lucide-react"
import { BrandLoader } from "@/components/brand-loader"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

import { BookingProvider, steps, useBooking } from "@/components/booking/booking-context"
import { StaffSelector } from "@/components/booking/staff-selector"
import { ServiceSelector } from "@/components/booking/service-selector"
import { DatePicker } from "@/components/booking/date-picker"
import { TimeSlotPicker } from "@/components/booking/time-slot-picker"
import { CustomerForm } from "@/components/booking/customer-form"
import { BookingConfirmation } from "@/components/booking/booking-confirmation"
import { formatCurrency, initialsFromName, slotLabel } from "@/components/booking/utils"

function AppHeader() {
  return (
    <header className="border-b border-zinc-800/60 bg-zinc-950 py-10">
      <div className="mx-auto flex max-w-lg flex-col items-center gap-4 px-4">
        <img
          src="/club-amsterdam-monogram.svg"
          alt="Club Amsterdam"
          className="h-20 w-20 animate-in fade-in zoom-in-75 rounded-3xl border border-amber-500/20 bg-black/50 p-3 duration-700"
        />
        <h1 className="animate-in fade-in slide-in-from-bottom-3 font-display text-4xl uppercase tracking-widest text-zinc-50 duration-700 delay-150">
          Club Amsterdam
        </h1>
      </div>
    </header>
  )
}

function StepProgress({ step }: { step: number }) {
  return (
    <div className="flex items-center gap-2">
      {steps.map((label, index) => (
        <div key={label} className="flex items-center gap-2">
          <div className={cn(
            "flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold transition-all duration-300",
            index < step ? "bg-amber-500/20 text-amber-400 scale-90" :
            index === step ? "bg-amber-500 text-zinc-950 scale-110 shadow-md shadow-amber-500/30" :
            "bg-zinc-800 text-zinc-500 scale-90"
          )}>
            {index < step ? "✓" : index + 1}
          </div>
          <span className={cn(
            "hidden text-xs transition-all duration-300 sm:block",
            index === step ? "text-zinc-200" : "text-zinc-600"
          )}>{label}</span>
          {index < steps.length - 1 && (
            <div className={cn(
              "mx-1 h-px w-6 transition-all duration-500",
              index < step ? "bg-amber-500/50" : "bg-zinc-800"
            )} />
          )}
        </div>
      ))}
    </div>
  )
}

function BookingSummaryBar() {
  const { selectedStaff, selectedService, date, slot, step } = useBooking()
  if (step === 0 || !selectedStaff || !selectedService) return null

  return (
    <div className="mb-4 flex animate-in fade-in slide-in-from-top-2 items-center gap-3 rounded-2xl border border-zinc-800 bg-black/30 px-4 py-3 duration-300">
      <Avatar className="h-9 w-9 shrink-0 border border-amber-500/15">
        <AvatarImage src={selectedStaff.avatar_url || undefined} alt={selectedStaff.name} />
        <AvatarFallback className="bg-zinc-800 text-xs">{initialsFromName(selectedStaff.name)}</AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold">{selectedStaff.name}</p>
        <p className="truncate text-xs text-zinc-400">{selectedService.name}</p>
      </div>
      <div className="shrink-0 text-right">
        {date && slot ? (
          <>
            <p className="text-xs font-medium text-amber-400">{date.slice(5).replace("-", "/")}</p>
            <p className="text-xs text-zinc-500">{slotLabel(slot.start)}</p>
          </>
        ) : (
          <Badge className="rounded-full bg-zinc-800 px-2 py-0.5 text-[10px] text-zinc-400">
            <Clock3 className="mr-1 h-3 w-3" />{selectedService.duration_minutes} min
          </Badge>
        )}
      </div>
    </div>
  )
}

function BookingWidgetInner() {
  const {
    catalog,
    loadingCatalog,
    catalogError,
    selectedStaff,
    selectedService,
    confirmedBooking,
    step,
    setStep,
    canContinue,
    handleConfirm,
    submitting,
    submitError,
  } = useBooking()

  const prevStepRef = useRef(step)
  const [slideDir, setSlideDir] = useState<"right" | "left">("right")

  useEffect(() => {
    setSlideDir(step > prevStepRef.current ? "right" : "left")
    prevStepRef.current = step
  }, [step])

  if (loadingCatalog) return <BrandLoader message="Cargando Club Amsterdam..." />

  if (catalogError || !catalog || !selectedStaff || !selectedService) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950 px-6">
        <div className="w-full max-w-sm animate-in fade-in zoom-in-95 rounded-3xl border border-red-500/30 bg-zinc-900/90 p-8 text-center duration-500">
          <AlertCircle className="mx-auto h-10 w-10 text-red-400" />
          <h2 className="mt-4 text-xl font-semibold">Agenda no disponible</h2>
          <p className="mt-2 text-sm text-zinc-400">{catalogError || "No se pudo cargar la agenda."}</p>
        </div>
      </div>
    )
  }

  if (confirmedBooking) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-50">
        <AppHeader />
        <div className="mx-auto max-w-lg px-4 py-6">
          <BookingConfirmation />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-50">
      <AppHeader />

      <main className="mx-auto max-w-lg px-4 py-6">
        {/* Progress */}
        <div className="mb-6 animate-in fade-in slide-in-from-top-3 duration-500 delay-300">
          <StepProgress step={step} />
        </div>

        {/* Summary bar (steps 1+2) */}
        <BookingSummaryBar />

        {/* Step content — re-mounts on step change to retrigger animation */}
        <div
          key={step}
          className={cn(
            "rounded-3xl border border-zinc-800/70 bg-zinc-900/60 p-5 animate-in fade-in duration-300",
            slideDir === "right" ? "slide-in-from-right-4" : "slide-in-from-left-4"
          )}
        >
          {step === 0 && (
            <div className="space-y-6">
              <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                <h2 className="font-display text-3xl uppercase leading-none">Elegí tu barbero</h2>
                <p className="mt-1 text-sm text-zinc-400">Seleccioná profesional y servicio.</p>
              </div>
              <StaffSelector />
              <ServiceSelector />
            </div>
          )}

          {step === 1 && (
            <div className="space-y-5">
              <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                <h2 className="font-display text-3xl uppercase leading-none">Elegí fecha y hora</h2>
                <p className="mt-1 text-sm text-zinc-400">Disponibilidad en tiempo real.</p>
              </div>
              <DatePicker />
              <TimeSlotPicker />
            </div>
          )}

          {step === 2 && (
            <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
              <CustomerForm />
              {submitError && (
                <p className="mt-3 text-sm text-red-300">{submitError}</p>
              )}
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="mt-4 flex animate-in fade-in slide-in-from-bottom-3 items-center justify-between gap-3 duration-500 delay-150">
          <Button
            variant="ghost"
            onClick={() => setStep((v) => Math.max(0, v - 1))}
            disabled={step === 0}
            className="rounded-2xl border border-zinc-800 px-5 text-zinc-400 transition-all hover:border-zinc-600 hover:text-zinc-200 active:scale-95"
          >
            <ChevronLeft className="mr-1 h-4 w-4" />Volver
          </Button>

          {step < steps.length - 1 ? (
            <Button
              onClick={() => setStep((v) => v + 1)}
              disabled={!canContinue()}
              className="flex-1 rounded-2xl bg-amber-500 font-semibold text-zinc-950 transition-all hover:bg-amber-400 hover:shadow-lg hover:shadow-amber-500/25 active:scale-95 disabled:opacity-40"
            >
              Continuar<ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          ) : (
            <Button
              onClick={handleConfirm}
              disabled={!canContinue() || submitting}
              className="flex-1 rounded-2xl bg-amber-500 font-semibold text-zinc-950 transition-all hover:bg-amber-400 hover:shadow-lg hover:shadow-amber-500/25 active:scale-95 disabled:opacity-40"
            >
              {submitting ? "Registrando..." : "Confirmar turno"}
            </Button>
          )}
        </div>

        {/* Price reminder on step 2 */}
        {step === 2 && selectedService && (
          <p className="mt-4 animate-in fade-in text-center text-xs text-zinc-500 duration-500">
            {selectedService.name} · {selectedService.duration_minutes} min · {formatCurrency(selectedService.price_amount, selectedService.price_currency)} (se paga en el local)
          </p>
        )}
      </main>

      <BusinessFooter />
    </div>
  )
}

function BusinessFooter() {
  const { catalog, mapEmbedUrl } = useBooking()
  if (!catalog) return null
  const { business } = catalog

  return (
    <footer className="mx-auto max-w-lg animate-in fade-in slide-in-from-bottom-4 space-y-3 px-4 pb-10 pt-4 duration-700 delay-500">
      {mapEmbedUrl ? (
        <div className="overflow-hidden rounded-3xl border border-zinc-800/60">
          <iframe
            title="Ubicación Club Amsterdam"
            src={mapEmbedUrl}
            className="h-52 w-full border-0"
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
          />
        </div>
      ) : null}

      <div className="rounded-3xl border border-zinc-800/60 bg-zinc-900/40 p-5 space-y-3">
        {business.address ? (
          <a
            href={business.maps_url || "#"}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-3 text-sm text-zinc-400 transition-colors hover:text-amber-400"
          >
            <MapPin className="h-4 w-4 shrink-0 text-amber-500/60" />
            {business.address}
          </a>
        ) : null}
        {business.phone ? (
          <a
            href={`tel:${business.phone}`}
            className="flex items-center gap-3 text-sm text-zinc-400 transition-colors hover:text-amber-400"
          >
            <Phone className="h-4 w-4 shrink-0 text-amber-500/60" />
            {business.phone}
          </a>
        ) : null}
        {business.instagram_url ? (
          <a
            href={business.instagram_url}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-3 text-sm text-zinc-400 transition-colors hover:text-amber-400"
          >
            <Instagram className="h-4 w-4 shrink-0 text-amber-500/60" />
            @clubamsterdam_
          </a>
        ) : null}
      </div>
    </footer>
  )
}

export function BookingWidget() {
  return (
    <BookingProvider>
      <BookingWidgetInner />
    </BookingProvider>
  )
}
