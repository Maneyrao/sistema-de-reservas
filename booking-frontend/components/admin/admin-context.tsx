"use client"

import { createContext, useContext, useEffect, useState, type ReactNode } from "react"

import {
  adminLogin,
  adminMe,
  createAdminBlock,
  createAdminBooking,
  getAdminBusiness,
  listAdminBlocks,
  listAdminBookings,
  listAdminServices,
  listAdminStaff,
  type AdminBooking,
  type AdminBusiness,
  type AdminService,
  type AdminStaff,
  type AdminTimeBlock,
  type AdminUser,
} from "@/lib/admin-api"

// ─── Constants ────────────────────────────────────────────────────────────────

export const SESSION_KEY = "club-amsterdam-admin-session"

export const DAY_OPTIONS = [
  { label: "Lunes", value: 0 },
  { label: "Martes", value: 1 },
  { label: "Miércoles", value: 2 },
  { label: "Jueves", value: 3 },
  { label: "Viernes", value: 4 },
  { label: "Sábado", value: 5 },
  { label: "Domingo", value: 6 },
]

// ─── Types ────────────────────────────────────────────────────────────────────

export type DashboardTab = "agenda" | "staff" | "services" | "business" | "blocks"

export type AvailabilityDraft = { weekday: number; start_time: string; end_time: string }

export type ServiceForm = {
  name: string
  slug: string
  duration_minutes: string
  price_amount: string
  price_currency: string
  active: boolean
}

export type StaffForm = {
  name: string
  slug: string
  title: string
  bio: string
  avatar_url: string
  active: boolean
  service_ids: number[]
  availability_rules: AvailabilityDraft[]
}

export type BlockForm = {
  staff_slug: string
  start_datetime: string
  end_datetime: string
  reason: string
  notes: string
}

export type BusinessForm = {
  name: string
  tagline: string
  hero_title: string
  hero_description: string
  announcement: string
  booking_note: string
  address: string
  phone: string
  instagram_url: string
  maps_url: string
}

export type BookingForm = {
  staff_slug: string
  service_slug: string
  date: string
  time: string
  first_name: string
  last_name: string
  phone: string
  email: string
  notes: string
  status: string
}

// ─── Utility helpers ──────────────────────────────────────────────────────────

export function isoDate(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`
}

export function startOfWeek(date = new Date()) {
  const next = new Date(date)
  next.setHours(0, 0, 0, 0)
  next.setDate(next.getDate() - ((next.getDay() + 6) % 7))
  return isoDate(next)
}

export function addDays(dateValue: string, days: number) {
  const date = new Date(`${dateValue}T00:00:00`)
  date.setDate(date.getDate() + days)
  return isoDate(date)
}

export function dateTimeInputValue(date = new Date()) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 16)
}

export function humanDateTime(value: string) {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat("es-AR", { dateStyle: "short", timeStyle: "short" }).format(date)
}

export function humanDayLabel(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString("es-AR", {
    weekday: "short",
    day: "numeric",
    month: "short",
  })
}

export function formatCurrency(amount: number, currency: string) {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amount)
}

export function normalizeSlug(value: string) {
  return value
    .toLowerCase()
    .trim()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
}

export function initialsFromName(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((value) => value[0]?.toUpperCase() ?? "")
    .join("")
}

export function timeToMinutes(value: string) {
  const [hours, minutes] = value.slice(0, 5).split(":").map(Number)
  return hours * 60 + minutes
}

export function statusClass(status: string) {
  return status === "completed"
    ? "bg-emerald-500/15 text-emerald-300"
    : status === "canceled"
      ? "bg-red-500/15 text-red-300"
      : status === "no_show"
        ? "bg-zinc-700 text-zinc-200"
        : "bg-amber-500/15 text-amber-300"
}

// ─── Empty form factories ─────────────────────────────────────────────────────

export function emptyServiceForm(): ServiceForm {
  return {
    name: "",
    slug: "",
    duration_minutes: "45",
    price_amount: "",
    price_currency: "ARS",
    active: true,
  }
}

export function emptyStaffForm(): StaffForm {
  return {
    name: "",
    slug: "",
    title: "",
    bio: "",
    avatar_url: "",
    active: true,
    service_ids: [],
    availability_rules: [{ weekday: 0, start_time: "13:45:00", end_time: "20:00:00" }],
  }
}

export function emptyBlockForm(staffSlug = ""): BlockForm {
  return {
    staff_slug: staffSlug,
    start_datetime: dateTimeInputValue(),
    end_datetime: dateTimeInputValue(new Date(Date.now() + 60 * 60 * 1000)),
    reason: "",
    notes: "",
  }
}

export function emptyBusinessForm(): BusinessForm {
  return {
    name: "",
    tagline: "",
    hero_title: "",
    hero_description: "",
    announcement: "",
    booking_note: "",
    address: "",
    phone: "",
    instagram_url: "",
    maps_url: "",
  }
}

export function emptyBookingForm(defaultStaff = ""): BookingForm {
  return {
    staff_slug: defaultStaff,
    service_slug: "",
    date: isoDate(new Date()),
    time: "14:00",
    first_name: "",
    last_name: "",
    phone: "",
    email: "",
    notes: "",
    status: "confirmed",
  }
}

// ─── Context shape ────────────────────────────────────────────────────────────

export type AdminContextValue = {
  // Auth
  authReady: boolean
  token: string | null
  adminUser: AdminUser | null
  isAuthenticated: boolean

  // Login form state
  loginEmail: string
  setLoginEmail: (value: string) => void
  loginPassword: string
  setLoginPassword: (value: string) => void
  loginError: string
  loginLoading: boolean
  handleLogin: (event: React.FormEvent<HTMLFormElement>) => Promise<void>

  // Business data
  business: AdminBusiness | null
  bookings: AdminBooking[]
  blocks: AdminTimeBlock[]
  services: AdminService[]
  staff: AdminStaff[]

  // Derived
  activeServices: AdminService[]
  activeStaff: AdminStaff[]
  weekStart: string
  weekEnd: string
  weekDays: string[]

  // Loading/error
  loadingData: boolean
  notice: { tone: "success" | "error"; text: string } | null

  // Active tab
  activeTab: DashboardTab
  setActiveTab: (tab: DashboardTab) => void

  // Week navigation
  setWeekStart: (value: string) => void

  // Shared actions
  logout: () => void
  loadSchedule: (currentToken: string) => Promise<void>
  flash: (tone: "success" | "error", text: string) => void

  // Booking detail modal state
  selectedBooking: AdminBooking | null
  setSelectedBooking: (booking: AdminBooking | null) => void
  busyBookingId: number | null
  setBusyBookingId: (id: number | null) => void

  // Create booking modal
  showCreateBooking: boolean
  setShowCreateBooking: (value: boolean) => void

  // Reschedule modal state
  rescheduleTarget: AdminBooking | null
  setRescheduleTarget: (booking: AdminBooking | null) => void
  rescheduleDate: string
  setRescheduleDate: (value: string) => void
  rescheduleTime: string
  setRescheduleTime: (value: string) => void
  rescheduleReason: string
  setRescheduleReason: (value: string) => void

  // Forms
  serviceForm: ServiceForm
  setServiceForm: React.Dispatch<React.SetStateAction<ServiceForm>>
  staffForm: StaffForm
  setStaffForm: React.Dispatch<React.SetStateAction<StaffForm>>
  blockForm: BlockForm
  setBlockForm: React.Dispatch<React.SetStateAction<BlockForm>>
  businessForm: BusinessForm
  setBusinessForm: React.Dispatch<React.SetStateAction<BusinessForm>>
  bookingForm: BookingForm
  setBookingForm: React.Dispatch<React.SetStateAction<BookingForm>>

  // Editing IDs
  editingServiceId: number | null
  setEditingServiceId: (id: number | null) => void
  editingStaffId: number | null
  setEditingStaffId: (id: number | null) => void

  // Refresh
  setBusiness: React.Dispatch<React.SetStateAction<AdminBusiness | null>>
  setBookings: React.Dispatch<React.SetStateAction<AdminBooking[]>>
  setBlocks: React.Dispatch<React.SetStateAction<AdminTimeBlock[]>>
  setServices: React.Dispatch<React.SetStateAction<AdminService[]>>
  setStaff: React.Dispatch<React.SetStateAction<AdminStaff[]>>
}

// ─── Context ──────────────────────────────────────────────────────────────────

const AdminContext = createContext<AdminContextValue | null>(null)

export function useAdminContext(): AdminContextValue {
  const ctx = useContext(AdminContext)
  if (!ctx) throw new Error("useAdminContext must be used inside AdminProvider")
  return ctx
}

// ─── Provider ─────────────────────────────────────────────────────────────────

export function AdminProvider({ children }: { children: ReactNode }) {
  const [authReady, setAuthReady] = useState(false)
  const [token, setToken] = useState<string | null>(null)
  const [adminUser, setAdminUser] = useState<AdminUser | null>(null)
  const [activeTab, setActiveTab] = useState<DashboardTab>("agenda")
  const [weekStart, setWeekStart] = useState(startOfWeek())
  const [business, setBusiness] = useState<AdminBusiness | null>(null)
  const [bookings, setBookings] = useState<AdminBooking[]>([])
  const [blocks, setBlocks] = useState<AdminTimeBlock[]>([])
  const [services, setServices] = useState<AdminService[]>([])
  const [staff, setStaff] = useState<AdminStaff[]>([])
  const [selectedBooking, setSelectedBooking] = useState<AdminBooking | null>(null)
  const [showCreateBooking, setShowCreateBooking] = useState(false)
  const [rescheduleTarget, setRescheduleTarget] = useState<AdminBooking | null>(null)
  const [rescheduleDate, setRescheduleDate] = useState("")
  const [rescheduleTime, setRescheduleTime] = useState("")
  const [rescheduleReason, setRescheduleReason] = useState("")
  const [notice, setNotice] = useState<{ tone: "success" | "error"; text: string } | null>(null)
  const [loadingData, setLoadingData] = useState(false)
  const [loginEmail, setLoginEmail] = useState("")
  const [loginPassword, setLoginPassword] = useState("")
  const [loginError, setLoginError] = useState("")
  const [loginLoading, setLoginLoading] = useState(false)
  const [serviceForm, setServiceForm] = useState<ServiceForm>(emptyServiceForm())
  const [staffForm, setStaffForm] = useState<StaffForm>(emptyStaffForm())
  const [blockForm, setBlockForm] = useState<BlockForm>(emptyBlockForm())
  const [businessForm, setBusinessForm] = useState<BusinessForm>(emptyBusinessForm())
  const [bookingForm, setBookingForm] = useState<BookingForm>(emptyBookingForm())
  const [editingServiceId, setEditingServiceId] = useState<number | null>(null)
  const [editingStaffId, setEditingStaffId] = useState<number | null>(null)
  const [busyBookingId, setBusyBookingId] = useState<number | null>(null)

  const weekEnd = addDays(weekStart, 6)
  const weekDays = Array.from({ length: 7 }, (_, index) => addDays(weekStart, index))
  const activeServices = services.filter((item) => item.active)
  const activeStaff = staff.filter((item) => item.active)

  function flash(tone: "success" | "error", text: string) {
    setNotice({ tone, text })
    if (typeof window !== "undefined") window.setTimeout(() => setNotice(null), 3200)
  }

  async function loadSchedule(currentToken: string) {
    const [nextBookings, nextBlocks] = await Promise.all([
      listAdminBookings(currentToken, { dateFrom: weekStart, dateTo: weekEnd }),
      listAdminBlocks(currentToken, { dateFrom: weekStart, dateTo: weekEnd }),
    ])
    setBookings(nextBookings)
    setBlocks(nextBlocks)
  }

  async function loadAll(currentToken: string) {
    setLoadingData(true)
    try {
      const [nextBusiness, nextServices, nextStaff] = await Promise.all([
        getAdminBusiness(currentToken),
        listAdminServices(currentToken),
        listAdminStaff(currentToken),
      ])
      setBusiness(nextBusiness)
      setBusinessForm({
        name: nextBusiness.name,
        tagline: nextBusiness.tagline || "",
        hero_title: nextBusiness.hero_title || "",
        hero_description: nextBusiness.hero_description || "",
        announcement: nextBusiness.announcement || "",
        booking_note: nextBusiness.booking_note || "",
        address: nextBusiness.address || "",
        phone: nextBusiness.phone || "",
        instagram_url: nextBusiness.instagram_url || "",
        maps_url: nextBusiness.maps_url || "",
      })
      setServices(nextServices)
      setStaff(nextStaff)
      setBookingForm((current) =>
        current.staff_slug ? current : emptyBookingForm(nextStaff.find((item) => item.active)?.slug || ""),
      )
      setBlockForm(emptyBlockForm(nextStaff.find((item) => item.active)?.slug || ""))
      await loadSchedule(currentToken)
    } catch (error) {
      flash("error", error instanceof Error ? error.message : "No se pudo cargar el dashboard")
    } finally {
      setLoadingData(false)
    }
  }

  useEffect(() => {
    if (!bookingForm.staff_slug && activeStaff[0])
      setBookingForm((current) => ({ ...current, staff_slug: activeStaff[0].slug }))
  }, [activeStaff, bookingForm.staff_slug])

  useEffect(() => {
    if (!bookingForm.staff_slug) return
    const nextServices = staff.find((item) => item.slug === bookingForm.staff_slug)?.services.filter((item) => item.active) ?? []
    if (nextServices.length && !nextServices.some((item) => item.slug === bookingForm.service_slug))
      setBookingForm((current) => ({ ...current, service_slug: nextServices[0].slug }))
  }, [bookingForm.service_slug, bookingForm.staff_slug, staff])

  useEffect(() => {
    let active = true
    if (typeof window !== "undefined") {
      const stored = window.sessionStorage.getItem(SESSION_KEY)
      if (stored) {
        try {
          const parsed = JSON.parse(stored) as { token: string; admin: AdminUser }
          if (active) {
            setToken(parsed.token)
            setAdminUser(parsed.admin)
          }
        } catch {
          window.sessionStorage.removeItem(SESSION_KEY)
        }
      }
    }
    if (active) setAuthReady(true)
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!token) return
    let active = true
    async function syncAdmin() {
      try {
        const me = await adminMe(token!)
        if (active) {
          setAdminUser(me)
          if (typeof window !== "undefined")
            window.sessionStorage.setItem(SESSION_KEY, JSON.stringify({ token, admin: me }))
        }
      } catch {
        if (active) logout()
      }
    }
    void syncAdmin()
    return () => {
      active = false
    }
  }, [token])

  useEffect(() => {
    if (token) void loadAll(token)
  }, [token, weekStart])

  function logout() {
    setToken(null)
    setAdminUser(null)
    if (typeof window !== "undefined") window.sessionStorage.removeItem(SESSION_KEY)
  }

  function persistSession(nextToken: string, nextAdmin: AdminUser) {
    setToken(nextToken)
    setAdminUser(nextAdmin)
    if (typeof window !== "undefined")
      window.sessionStorage.setItem(SESSION_KEY, JSON.stringify({ token: nextToken, admin: nextAdmin }))
  }

  async function handleLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoginError("")
    setLoginLoading(true)
    try {
      const payload = await adminLogin(loginEmail.trim(), loginPassword)
      persistSession(payload.access_token, payload.admin)
    } catch (error) {
      setLoginError(error instanceof Error ? error.message : "No se pudo iniciar sesión")
    } finally {
      setLoginLoading(false)
    }
  }

  const value: AdminContextValue = {
    authReady,
    token,
    adminUser,
    isAuthenticated: !!token && !!adminUser,
    loginEmail,
    setLoginEmail,
    loginPassword,
    setLoginPassword,
    loginError,
    loginLoading,
    handleLogin,
    business,
    bookings,
    blocks,
    services,
    staff,
    activeServices,
    activeStaff,
    weekStart,
    weekEnd,
    weekDays,
    loadingData,
    notice,
    activeTab,
    setActiveTab,
    setWeekStart,
    logout,
    loadSchedule,
    flash,
    selectedBooking,
    setSelectedBooking,
    busyBookingId,
    setBusyBookingId,
    showCreateBooking,
    setShowCreateBooking,
    rescheduleTarget,
    setRescheduleTarget,
    rescheduleDate,
    setRescheduleDate,
    rescheduleTime,
    setRescheduleTime,
    rescheduleReason,
    setRescheduleReason,
    serviceForm,
    setServiceForm,
    staffForm,
    setStaffForm,
    blockForm,
    setBlockForm,
    businessForm,
    setBusinessForm,
    bookingForm,
    setBookingForm,
    editingServiceId,
    setEditingServiceId,
    editingStaffId,
    setEditingStaffId,
    setBusiness,
    setBookings,
    setBlocks,
    setServices,
    setStaff,
  }

  return <AdminContext.Provider value={value}>{children}</AdminContext.Provider>
}
