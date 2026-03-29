# CLAUDE.md — Sistema de Reservas Club Amsterdam

## Proyecto

Sistema multi-tenant de reservas para barbería. Backend FastAPI + SQLAlchemy 2.0, frontend Next.js 16 + Shadcn/ui. Base de datos SQLite (dev) / PostgreSQL (prod).

## Stack

- **Backend:** Python 3.11+, FastAPI 0.104+, SQLAlchemy 2.0, Alembic, PyJWT, passlib
- **Frontend:** Next.js 16, React 19, Tailwind CSS, Shadcn/ui, Framer Motion, Recharts
- **DB:** SQLite con WAL (dev), PostgreSQL (prod target)
- **Auth:** JWT para admin, public_token (UUID hex) para clientes

## Estructura de directorios

```
├── main.py                    # Entry point FastAPI
├── database/                  # Engine, session factory, Base
├── models/                    # SQLAlchemy ORM (Business, Staff, Service, Booking, Customer, etc.)
├── schemas/                   # Pydantic request/response
├── services/                  # Lógica de negocio (booking, availability, auth, audit, etc.)
├── routers/                   # Endpoints FastAPI (public v1 + admin)
├── dependencies/              # Inyección de dependencias (JWT auth)
├── alembic/                   # Migraciones
├── scripts/                   # Seeds, init DB, tests manuales
├── booking-frontend/          # ✅ Frontend canónico (Next.js 16)
├── admin-dashboard/           # ⚠️ DEPRECADO — Vite alternativo
└── frontend-public/           # ⚠️ DEPRECADO — alternativo antiguo
```

## Convenciones de código

### Python (Backend)
- Type hints obligatorios en todas las funciones públicas
- Keyword-only arguments con `*` en funciones de servicio
- Excepciones de dominio tipadas (SlotNotAvailable, BookingNotFound, InvalidBookingRequest)
- Queries siempre filtradas por `business_id` (multi-tenant boundary)
- Timezone: usar `datetime.now(timezone.utc)`, NUNCA `datetime.utcnow`
- Sesiones: transacciones explícitas con `db.begin()` en routers

### TypeScript (Frontend)
- Componentes funcionales con hooks
- Shadcn/ui para primitivas UI
- `cn()` para merge de clases Tailwind
- API client centralizado en `lib/api.ts` y `lib/admin-api.ts`
- Locale: `es-AR` para formatos de fecha, moneda y hora

### Base de datos
- Slugs únicos por business para Staff y Service
- Intervalos semiabiertos `[start, end)` para bookings y disponibilidad
- Slots alineados a bloques de 15 minutos
- Idempotency key único por business para prevenir duplicados

## Comandos útiles

```bash
# Backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
alembic upgrade head
python scripts/seed.py
python scripts/create_admin_user.py

# Frontend (booking-frontend/)
cd booking-frontend && npm run dev
cd booking-frontend && npm run build

# Tests (pendiente migrar a pytest)
python scripts/test_all_endpoints.py
```

## Variables de entorno requeridas

```
DATABASE_URL=sqlite:///./booking_local.db   # o postgresql://...
CRON_SECRET=<secret-para-cron>
ADMIN_JWT_SECRET=<secret-para-jwt>
ADMIN_JWT_EXPIRE_MINUTES=720
ALLOWED_ORIGINS=http://localhost:3000       # pendiente implementar
```

## Problemas conocidos (tech debt)

1. CORS abierto a `*` — restringir a ALLOWED_ORIGINS
2. BUSINESS_TZ hardcodeado en availability_service.py y booking_service.py — debe leerse del modelo Business
3. `datetime.utcnow` en models/booking.py — migrar a `datetime.now(timezone.utc)`
4. Sin exception handlers globales en main.py
5. booking-widget.tsx (29KB) y admin-dashboard.tsx (54KB) monolíticos
6. Sin tests automatizados (pytest)
7. admin-dashboard/ y frontend-public/ probablemente deprecados
8. WhatsApp service es un stub sin implementación real
