"""
WebSocket endpoint para notificaciones en tiempo real al panel de admin.

Protocolo:
- El cliente conecta: ws://host/ws/admin/{business_slug}?token=<JWT>
- El servidor valida el JWT y el business_slug.
- El servidor envía mensajes JSON cuando hay nuevas reservas o cambios de estado.
- El cliente puede enviar "ping" para mantener la conexión viva.

Arquitectura interna:
- ConnectionManager mantiene un dict de conexiones por business_id.
- Los routers HTTP llaman a `ws_manager.broadcast()` después de crear/cancelar bookings.
- El manager es un singleton importable desde cualquier router.
"""
import json
import logging
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from database.session import SessionLocal
from services.admin_auth_service import decode_admin_access_token as decode_access_token, AdminAuthError
from models.admin_user import AdminUser
from models.business import Business
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Administra conexiones WebSocket agrupadas por business_id."""

    def __init__(self) -> None:
        # business_id → set of active WebSocket connections
        self._connections: dict[int, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, business_id: int) -> None:
        await websocket.accept()
        self._connections.setdefault(business_id, set()).add(websocket)
        logger.info("WS connected business_id=%s total=%s", business_id, len(self._connections[business_id]))

    def disconnect(self, websocket: WebSocket, business_id: int) -> None:
        conns = self._connections.get(business_id, set())
        conns.discard(websocket)
        if not conns:
            self._connections.pop(business_id, None)
        logger.info("WS disconnected business_id=%s remaining=%s", business_id, len(conns))

    async def broadcast(self, business_id: int, event: dict[str, Any]) -> None:
        """Envía un evento JSON a todos los admins conectados del negocio."""
        conns = self._connections.get(business_id, set())
        if not conns:
            return
        message = json.dumps(event, ensure_ascii=False, default=str)
        dead: list[WebSocket] = []
        for ws in list(conns):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, business_id)

    def active_count(self, business_id: int) -> int:
        return len(self._connections.get(business_id, set()))


# Singleton accesible desde otros módulos
ws_manager = ConnectionManager()


def _authenticate_ws(token: str) -> AdminUser | None:
    """Valida el JWT y retorna el AdminUser. Retorna None si inválido."""
    db: Session = SessionLocal()
    try:
        payload = decode_access_token(token)
        admin_id = payload.get("sub")
        if not admin_id:
            return None
        admin = db.execute(
            select(AdminUser).where(AdminUser.id == int(admin_id), AdminUser.is_active.is_(True))
        ).scalar_one_or_none()
        return admin
    except (AdminAuthError, Exception):
        return None
    finally:
        db.close()


@router.websocket("/ws/admin/{business_slug}")
async def admin_ws_endpoint(
    websocket: WebSocket,
    business_slug: str,
    token: str = Query(..., description="JWT de autenticación admin"),
):
    """
    WebSocket de notificaciones para administradores.

    Eventos del servidor:
    - {"event": "booking_created", "booking_id": int, "staff_slug": str, ...}
    - {"event": "booking_cancelled", "booking_id": int, ...}
    - {"event": "booking_status_updated", "booking_id": int, "new_status": str}
    - {"event": "pong"}
    """
    admin = _authenticate_ws(token)
    if admin is None:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    # Validar que el business_slug corresponda al negocio del admin
    db: Session = SessionLocal()
    try:
        business = db.execute(
            select(Business).where(
                Business.id == admin.business_id,
                Business.slug == business_slug,
            )
        ).scalar_one_or_none()
    finally:
        db.close()

    if not business:
        await websocket.close(code=4004, reason="Business not found")
        return

    await ws_manager.connect(websocket, admin.business_id)
    try:
        # Enviar evento de bienvenida
        await websocket.send_text(json.dumps({
            "event": "connected",
            "business_id": admin.business_id,
            "admin_name": admin.full_name,
        }))

        while True:
            data = await websocket.receive_text()
            if data.strip().lower() == "ping":
                await websocket.send_text(json.dumps({"event": "pong"}))

    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(websocket, admin.business_id)
