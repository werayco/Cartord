import asyncio
import os
from logging.config import fileConfig
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[3] / "shared" / "compose_files" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

from sqlalchemy import pool
from sqlalchemy.engine import Connection  # noqa: E402
from sqlalchemy.ext.asyncio import async_engine_from_config  # noqa: E402
from app.models.product import Inventory  # noqa: E402
from app.models.outbox import OutboxEvent  # noqa: E402
from app.db.session import Base  # noqa: E402
from alembic import context  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

db_url = os.getenv("INVENTORY_DATABASE_URL", "").replace("@postgres:", "@localhost:")
config.set_main_option("sqlalchemy.url", db_url)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()