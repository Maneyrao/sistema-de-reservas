import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.base import Base
from database.session import engine
import models  # noqa: F401
from scripts.seed import run_seed


def init_local_db() -> None:
    Base.metadata.create_all(bind=engine)
    run_seed()
    print("Local DB lista.")


if __name__ == "__main__":
    init_local_db()
