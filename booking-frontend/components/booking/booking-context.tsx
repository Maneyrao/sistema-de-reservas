"use client"

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { createBooking, getAvailability, getPublicCatalog, type AvailabilitySlot, type BookingResponse, type PublicCatalog } from "@/lib/api"
import { buildMapEmbedUrl, formatDateValue, nextDays } from "@/components/booking/utils"

export type CustomerForm = { firstName: string; lastName: string; phone: string; email: string; notes: string }

export const steps = ["Tu barbero", "Fecha y hora", "Tus datos"]

interface BookingContextValue {
  catalog: PublicCatalog | null
  selectedStaffSlug: string | null
  selectedServiceSlug: string | null
  date: string | null
  slot: AvailabilitySlot | null
  slots: AvailabilitySlot[]
  customer: CustomerForm
  loadingCatalog: boolean
  loadingSlots: boolean
  submitting: boolean
  catalogError: string | null
  slotError: string | null
  submitError: string | null
  confirmedBooking: BookingResponse | null
  setSelectedStaffSlug: (slug: string | null) => void
  setSelectedServiceSlug: (slug: string | null) => void
  setDate: (date: string | null) => void
  setSlot: (slot: AvailabilitySlot | null) => void
  setCustomer: React.Dispatch<React.SetStateAction<CustomerForm>>
  selectedStaff: PublicCatalog["staff"][number] | null
  availableServices: PublicCatalog["services"]
  selectedService: PublicCatalog["services"][number] | null
  days: { key: string; value: Date }[]
  customerValid: boolean
  mapEmbedUrl: string | null
  step: number
  setStep: React.Dispatch<React.SetStateAction<number>>
  goNext: () => void
  goBack: () => void
  canContinue: () => boolean
  getContinueHint: () => string | null
  handleConfirm: () => Promise<void>
  resetBooking: () => void
}

const BookingContext = createContext<BookingContextValue | null>(null)

export function useBooking() {
  const ctx = useContext(BookingContext)
  if (!ctx) throw new Error("useBooking must be used inside BookingProvider")
  return ctx
}

export function BookingProvider({ children }: { children: ReactNode }) {
  const [step, setStep] = useState(0)
  const [catalog, setCatalog] = useState<PublicCatalog | null>(null)
  const [selectedStaffSlug, setSelectedStaffSlug] = useState<string | null>(null)
  const [selectedServiceSlug, setSelectedServiceSlug] = useState<string | null>(null)
  const [date, setDate] = useState<string | null>(null)
  const [slot, setSlot] = useState<AvailabilitySlot | null>(null)
  const [slots, setSlots] = useState<AvailabilitySlot[]>([])
  const [customer, setCustomer] = useState<CustomerForm>({ firstName: "", lastName: "", phone: "", email: "", notes: "" })
  const [loadingCatalog, setLoadingCatalog] = useState(true)
  const [loadingSlots, setLoadingSlots] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [catalogError, setCatalogError] = useState<string | null>(null)
  const [slotError, setSlotError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [confirmedBooking, setConfirmedBooking] = useState<BookingResponse | null>(null)

  const selectedStaff = catalog?.staff.find((item) => item.slug === selectedStaffSlug) ?? null
  const availableServices = selectedStaff
    ? (catalog?.services ?? []).filter((item) => selectedStaff.service_slugs.includes(item.slug))
    : []
  const selectedService = availableServices.find((item) => item.slug === selectedServiceSlug) ?? null
  const days = nextDays(Math.min(catalog?.booking_rules.max_advance_days ?? 14, 15))
  const customerValid =
    customer.firstName.trim().length >= 2 &&
    customer.lastName.trim().length >= 2 &&
    customer.phone.trim().replace(/\D/g, "").length >= 8
  const mapEmbedUrl = buildMapEmbedUrl(catalog?.business.maps_url ?? null)

  useEffect(() => {
    let active = true
    async function loadCatalog() {
      try {
        const data = await getPublicCatalog()
        if (!active) return
        const defaultStaff = data.staff.find((item) => item.slug === data.booking_rules.default_staff_slug) ?? data.staff[0] ?? null
        const defaultService = data.services.find((item) => defaultStaff?.service_slugs.includes(item.slug)) ?? null
        setCatalog(data)
        setSelectedStaffSlug(defaultStaff?.slug ?? null)
        setSelectedServiceSlug(defaultService?.slug ?? null)
      } catch (error) {
        if (active) setCatalogError(error instanceof Error ? error.message : "No se pudo cargar el catalogo.")
      } finally {
        if (active) setLoadingCatalog(false)
      }
    }
    void loadCatalog()
    return () => { active = false }
  }, [])

  useEffect(() => {
    if (!catalog) return
    const currentStaff = catalog.staff.find((item) => item.slug === selectedStaffSlug) ?? null
    const offeredServices = currentStaff
      ? catalog.services.filter((item) => currentStaff.service_slugs.includes(item.slug))
      : []
    if (!selectedServiceSlug || !offeredServices.some((item) => item.slug === selectedServiceSlug)) {
      setSelectedServiceSlug(offeredServices[0]?.slug ?? null)
      setSlot(null)
    }
  }, [catalog, selectedServiceSlug, selectedStaffSlug])

  useEffect(() => {
    if (!selectedService || !selectedStaff || !date) {
      setSlots([])
      return
    }
    let active = true
    async function loadSlots() {
      setLoadingSlots(true)
      setSlotError(null)
      try {
        const response = await getAvailability({
          serviceSlug: selectedService!.slug,
          staffSlug: selectedStaff!.slug,
          date: date!,
        })
        if (!active) return
        setSlots(response)
        if (slot && !response.some((item) => item.start === slot.start)) setSlot(null)
      } catch (error) {
        if (active) {
          setSlots([])
          setSlotError(error instanceof Error ? error.message : "No se pudo consultar la agenda.")
        }
      } finally {
        if (active) setLoadingSlots(false)
      }
    }
    void loadSlots()
    return () => { active = false }
  }, [date, selectedService?.slug, selectedStaff?.slug, slot])

  function canContinue() {
    if (step === 0) return selectedStaff !== null && selectedService !== null
    if (step === 1) return date !== null && slot !== null
    return customerValid
  }

  function getContinueHint(): string | null {
    if (canContinue()) return null
    if (step === 0) {
      if (!selectedStaff) return "Elegí quién te va a cortar"
      if (!selectedService) return "Seleccioná el servicio que querés"
    }
    if (step === 1) {
      if (!date) return "Elegí una fecha para ver los horarios"
      if (!slot) return "Seleccioná el horario que más te queda"
    }
    if (step === 2) {
      if (customer.firstName.trim().length < 2) return "Ingresá tu nombre para reservar"
      if (customer.lastName.trim().length < 2) return "Falta tu apellido"
      if (customer.phone.trim().replace(/\D/g, "").length < 8) return "Ingresá un WhatsApp válido"
    }
    return null
  }

  function goNext() { setStep((v) => v + 1) }
  function goBack() { setStep((v) => Math.max(0, v - 1)) }

  function resetBooking() {
    setStep(0)
    setDate(null)
    setSlot(null)
    setSlots([])
    setSubmitError(null)
    setConfirmedBooking(null)
    setCustomer({ firstName: "", lastName: "", phone: "", email: "", notes: "" })
  }

  async function handleConfirm() {
    if (!selectedService || !selectedStaff || !date || !slot || !customerValid) return
    setSubmitting(true)
    setSubmitError(null)
    try {
      const response = await createBooking({
        service_slug: selectedService.slug,
        staff_slug: selectedStaff.slug,
        date,
        time: slot.start.slice(11, 19),
        customer: {
          first_name: customer.firstName.trim(),
          last_name: customer.lastName.trim(),
          phone: customer.phone.trim(),
          ...(customer.email.trim() ? { email: customer.email.trim() } : {}),
        },
        ...(customer.notes.trim() ? { notes: customer.notes.trim() } : {}),
      })
      setConfirmedBooking(response)
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "No se pudo registrar la reserva.")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <BookingContext.Provider
      value={{
        catalog, selectedStaffSlug, selectedServiceSlug, date, slot, slots, customer,
        loadingCatalog, loadingSlots, submitting, catalogError, slotError, submitError, confirmedBooking,
        setSelectedStaffSlug, setSelectedServiceSlug, setDate, setSlot, setCustomer,
        selectedStaff, availableServices, selectedService, days, customerValid, mapEmbedUrl,
        step, setStep, goNext, goBack, canContinue, getContinueHint, handleConfirm, resetBooking,
      }}
    >
      {children}
    </BookingContext.Provider>
  )
}
