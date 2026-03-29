"""
Fixtures globales de pytest para el sistema de reservas.

Estrategia:
- SQLite en memoria con StaticPool → una sola conexión compartida por test.
  Esto es necesario porque SQLite :memory: es por-conexión: cada nueva
  conexión obtiene una base de datos vacía. Con StaticPool todas las sesiones
  comparten la misma conexión subyacente.
- Tablas creadas antes de cada test y eliminadas al finalizar (autouse).
- TestClient recibe la misma sesión que el código de setup → los datos son visibles.
"""
import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Configurar variables de entorno ANTES de importar la app
os.environ.setdefault("ADMIN_JWT_SECRET", "test-secret-key-for-testing-only")
os.environ.setdefault("CRON_SECRET", "test-cron-secret")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from database.session import get_db  # noqa: E402
from main import app  # noqa: E402
from models import Base  # noqa: E402


# ---------------------------------------------------------------------------
# Motor SQLite en memoria — StaticPool para compartir conexión
# ---------------------------------------------------------------------------

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)


@event.listens_for(test_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


@pytest.fixture(autouse=True)
def setup_db():
    """Crea todas las tablas antes de cada test y las elimina al finalizar."""
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture()
def db_session(setup_db) -> Generator[Session, None, None]:
    """Sesión de DB aislada por test. Rollback automático al finalizar."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    TestClient de FastAPI con la DB de test inyectada.

    El override de get_db devuelve la misma db_session que se usó en el
    setup del test, por lo que los datos insertados son visibles al cliente.
    """

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()
