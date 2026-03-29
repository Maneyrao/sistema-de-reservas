import { API_BASE_URL, BUSINESS_SLUG } from "@/lib/api"

export type AdminUser = {
  id: number
  business_id: number
  full_name: string
  email: string
  role: string
  is_active: boolean
  last_login_at: string | null
}

export type AdminLoginResponse = {
  access_token: string
  token_type: string
  expires_in_seconds: number
  admin: AdminUser
}

export type AdminBooking = {
  id: number
  status: string
  start_datetime: string
  end_datetime: string
  customer_name: string
  customer_phone: string | null
  customer_email: string | null
  service_name: string
  service_slug: string
  staff_name: string
  staff_slug: string
  notes: string | null
  canceled_reason: string | null
  created_at: string
}

export type AdminTimeBlock = {
  id: number
  staff_id: number | null
  staff_slug: string | null
  start_datetime: string
  end_datetime: string
  reason: string | null
  notes: string | null
  created_by_admin_id: number | null
  created_at: string
}

export type AdminService = {
  id: number
  name: string
  slug: string
  duration_minutes: number
  price_amount: number
  price_currency: string
  active: boolean
}

export type AdminAvailabilityRule = {
  id: number
  weekday: number
  start_time: string
  end_time: string
}

export type AdminStaff = {
  id: number
  name: string
  slug: string
  title: string | null
  bio: string | null
  avatar_url: string | null
  active: boolean
  services: AdminService[]
  availability_rules: AdminAvailabilityRule[]
}

export type AdminBusiness = {
  id: number
  slug: string
  name: string
  timezone: string
  tagline: string | null
  hero_title: string | null
  hero_description: string | null
  announcement: string | null
  booking_note: string | null
  address: string | null
  phone: string | null
  instagram_url: string | null
  maps_url: string | null
}

export type AdminActivity = {
  id: number
  action: string
  entity_type: string
  entity_id: string
  admin_name: string | null
  payload_json: string | null
  created_at: string
}

function buildUrl(path: string, query?: Record<string, string | string[] | undefined>) {
  const url = new URL(path, API_BASE_URL)

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value === undefined || value === "") return
      if (Array.isArray(value)) {
        value.forEach((item) => url.searchParams.append(key, item))
        return
      }
      url.searchParams.set(key, value)
    })
  }

  return url.toString()
}

async function adminRequest<T>(
  path: string,
  init?: RequestInit & {
    token?: string
    query?: Record<string, string | string[] | undefined>
  },
): Promise<T> {
  const response = await fetch(buildUrl(path, init?.query), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.token ? { Authorization: `Bearer ${init.token}` } : {}),
      ...(init?.headers || {}),
    },
    cache: "no-store",
  })

  const text = await response.text()
  let payload: unknown = null

  try {
    payload = text ? JSON.parse(text) : null
  } catch {
    payload = text
  }

  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : text || "Request failed"
    throw new Error(detail)
  }

  return payload as T
}

export function adminLogin(email: string, password: string) {
  return adminRequest<AdminLoginResponse>("/admin/auth/login", {
    method: "POST",
    body: JSON.stringify({
      business_slug: BUSINESS_SLUG,
      email,
      password,
    }),
  })
}

export function adminMe(token: string) {
  return adminRequest<AdminUser>("/admin/auth/me", { token })
}

export async function listAdminBookings(token: string, params: { dateFrom: string; dateTo: string; status?: string[] }): Promise<AdminBooking[]> {
  const response = await adminRequest<{ items: AdminBooking[] } | AdminBooking[]>("/admin/bookings", {
    token,
    query: {
      date_from: params.dateFrom,
      date_to: params.dateTo,
      status: params.status,
    },
  })
  return Array.isArray(response) ? response : (response as { items: AdminBooking[] }).items ?? []
}

export function createAdminBooking(
  token: string,
  payload: {
    staff_slug: string
    service_slug: string
    date: string
    time: string
    customer: {
      first_name: string
      last_name: string
      phone: string
      email?: string
    }
    notes?: string | null
    status?: string
  },
) {
  return adminRequest<AdminBooking>("/admin/bookings", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  })
}

export function cancelAdminBooking(token: string, bookingId: number, reason: string | null) {
  return adminRequest<AdminBooking>(`/admin/bookings/${bookingId}/cancel`, {
    method: "POST",
    token,
    body: JSON.stringify({ reason }),
  })
}

export function rescheduleAdminBooking(
  token: string,
  bookingId: number,
  payload: { new_date: string; new_time: string; reason?: string | null },
) {
  return adminRequest<AdminBooking>(`/admin/bookings/${bookingId}/reschedule`, {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  })
}

export function updateAdminBookingStatus(
  token: string,
  bookingId: number,
  payload: { status: string; reason?: string | null },
) {
  return adminRequest<AdminBooking>(`/admin/bookings/${bookingId}/status`, {
    method: "PATCH",
    token,
    body: JSON.stringify(payload),
  })
}

export function listAdminBlocks(token: string, params: { dateFrom: string; dateTo: string; staffSlug?: string }) {
  return adminRequest<AdminTimeBlock[]>("/admin/blocks", {
    token,
    query: {
      date_from: params.dateFrom,
      date_to: params.dateTo,
      staff_slug: params.staffSlug,
    },
  })
}

export function createAdminBlock(
  token: string,
  payload: {
    staff_slug?: string | null
    start_datetime: string
    end_datetime: string
    reason?: string | null
    notes?: string | null
  },
) {
  return adminRequest<AdminTimeBlock>("/admin/blocks", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  })
}

export function deleteAdminBlock(token: string, blockId: number) {
  return adminRequest<{ deleted: boolean; id: number }>(`/admin/blocks/${blockId}`, {
    method: "DELETE",
    token,
  })
}

export function getAdminBusiness(token: string) {
  return adminRequest<AdminBusiness>("/admin/business", { token })
}

export function updateAdminBusiness(token: string, payload: Partial<Omit<AdminBusiness, "id" | "slug" | "timezone">>) {
  return adminRequest<AdminBusiness>("/admin/business", {
    method: "PATCH",
    token,
    body: JSON.stringify(payload),
  })
}

export function listAdminActivity(token: string, limit = 20) {
  return adminRequest<AdminActivity[]>("/admin/business/activity", {
    token,
    query: { limit: String(limit) },
  })
}

export function listAdminServices(token: string) {
  return adminRequest<AdminService[]>("/admin/services", { token })
}

export function createAdminService(token: string, payload: Omit<AdminService, "id">) {
  return adminRequest<AdminService>("/admin/services", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  })
}

export function updateAdminService(
  token: string,
  serviceId: number,
  payload: Partial<Omit<AdminService, "id">>,
) {
  return adminRequest<AdminService>(`/admin/services/${serviceId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(payload),
  })
}

export function deleteAdminService(token: string, serviceId: number) {
  return adminRequest<AdminService>(`/admin/services/${serviceId}`, {
    method: "DELETE",
    token,
  })
}

export function listAdminStaff(token: string) {
  return adminRequest<AdminStaff[]>("/admin/staff", { token })
}

export function createAdminStaff(
  token: string,
  payload: {
    name: string
    slug: string
    title?: string | null
    bio?: string | null
    avatar_url?: string | null
    active: boolean
    service_ids: number[]
    availability_rules: Array<{ weekday: number; start_time: string; end_time: string }>
  },
) {
  return adminRequest<AdminStaff>("/admin/staff", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  })
}

export function updateAdminStaff(
  token: string,
  staffId: number,
  payload: {
    name?: string
    slug?: string
    title?: string | null
    bio?: string | null
    avatar_url?: string | null
    active?: boolean
    service_ids?: number[]
    availability_rules?: Array<{ weekday: number; start_time: string; end_time: string }>
  },
) {
  return adminRequest<AdminStaff>(`/admin/staff/${staffId}`, {
    method: "PATCH",
    token,
    body: JSON.stringify(payload),
  })
}

export function deleteAdminStaff(token: string, staffId: number) {
  return adminRequest<AdminStaff>(`/admin/staff/${staffId}`, {
    method: "DELETE",
    token,
  })
}
