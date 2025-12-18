from logging.config import fileConfig
import os, sys
from dotenv import load_dotenv

from alembic import context
from sqlalchemy import create_engine

sys.path.append(os.getcwd())
load_dotenv()

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# IMPORTS REALES (ajustalos a tus clases/archivos)
from database.base import Base
from models.booking import Booking
from models.business import Business
from models.customer import Customer    
from models.service import Service
from models.staff import Staff
from models.availability import AvailabilityRule


target_metadata = Base.metadata

def run_migrations_offline():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    connectable = create_engine(database_url)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
