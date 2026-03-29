export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000"

export const BUSINESS_SLUG =
  process.env.NEXT_PUBLIC_BUSINESS_SLUG || "club-amsterdam"

export interface PublicStaff {
  slug: string
  name: string
  title: string | null
  bio: string | null
  avatar_url: string | null
  service_slugs: string[]
}

export interface PublicService {
  slug: string
  name: string
  duration_minutes: number
  price_amount: number
  price_currency: string
}

export interface PublicCatalog {
  business: {
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
  staff: PublicStaff[]
  services: PublicService[]
  booking_rules: {
    slot_step_minutes: number
    max_advance_days: number
    default_staff_slug: string
  }
}

export interface AvailabilitySlot {
  start: string
  end: string
}

export interface CreateBookingPayload {
  service_slug: string
  staff_slug: string
  date: string
  time: string
  customer: {
    first_name: string
    last_name: string
    phone: string
    email?: string
  }
  notes?: string
}

export interface BookingResponse {
  id: number
  status: string
  business_slug: string
  staff_slug: string | null
  service_slug: string | null
  service_name: string | null
  customer_name: string | null
  customer_phone: string | null
  start_datetime: string
  end_datetime: string
  public_token: string
  idempotency_key: string | null
  notes: string | null
}

function buildUrl(path: string, query?: Record<string, string>) {
  const url = new URL(path, API_BASE_URL)

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (!value) return
      url.searchParams.set(key, value)
    })
  }

  return url.toString()
}

async function apiRequest<T>(
  path: string,
  init?: RequestInit & {
    query?: Record<string, string>
  },
): Promise<T> {
  const response = await fetch(buildUrl(path, init?.query), {
    ...init,
    headers: {
      "Content-Type": "application/json",
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
    const message =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? String((payload as { detail: unknown }).detail)
        : text || "Request failed"
    throw new Error(message)
  }

  return payload as T
}

export function getPublicCatalog() {
  return apiRequest<PublicCatalog>(`/v1/business/${BUSINESS_SLUG}/catalog`)
}

export function getAvailability(params: {
  serviceSlug: string
  staffSlug: string
  date: string
}) {
  return apiRequest<AvailabilitySlot[]>(
    `/v1/business/${BUSINESS_SLUG}/availability/slots`,
    {
      query: {
        service_slug: params.serviceSlug,
        staff_slug: params.staffSlug,
        date_from: params.date,
        date_to: params.date,
      },
    },
  )
}

export function createBooking(payload: CreateBookingPayload) {
  return apiRequest<BookingResponse>(`/v1/business/${BUSINESS_SLUG}/bookings`, {
    method: "POST",
    headers: {
      "Idempotency-Key":
        typeof crypto !== "undefined" && "randomUUID" in crypto
          ? crypto.randomUUID()
          : `booking-${Date.now()}`,
    },
    body: JSON.stringify(payload),
  })
}
