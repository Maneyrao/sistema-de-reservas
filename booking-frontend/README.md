# Club Amsterdam Booking Frontend

Frontend publico en Next.js conectado al backend local del sistema de reservas de Club Amsterdam.

## Variables de entorno

Copia `.env.example` a `.env.local` y ajusta si hace falta:

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
NEXT_PUBLIC_BUSINESS_SLUG=club-amsterdam
```

## Desarrollo

```bash
npm install
npm run dev
```

## Flujo integrado

Este frontend consume:

- `GET /v1/business/{business_slug}/catalog`
- `GET /v1/business/{business_slug}/availability/slots`
- `POST /v1/business/{business_slug}/bookings`

La semilla inicial deja cargado:

- Matias Damonte
- admin owner unico
- horario base todos los dias de 13:45 a 20:00
- servicios:
  - Corte de Barba
  - Corte de Cabello
  - Corte de Cabello + Barba
  - Limpieza facial

El frontend publico permite:

- elegir barbero
- elegir entre los servicios asignados a ese barbero
- consultar disponibilidad real
- registrar la reserva directo en el backend
