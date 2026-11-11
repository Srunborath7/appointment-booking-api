import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import your application models and configuration
from app.core.config import settings
from app.core.database import Base
import app.domain.auth.model  # noqa: F401 - Register models with Base.metadata
import app.domain.patient.model  # noqa: F401 - Register patient model with Base.metadata


def normalize_database_url(url: str) -> str:
    """Ensure the URL uses an async driver compatible with Alembic async engine."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+" not in url.split("://")[0]:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set database URL dynamically from app settings (.env)
raw_url = settings.DATABASE_URL or config.get_main_option("sqlalchemy.url")
target_url = normalize_database_url(raw_url) if raw_url else None

if target_url:
    # Escape '%' as '%%' for configparser to prevent interpolation syntax error with encoded passwords
    config.set_main_option("sqlalchemy.url", target_url.replace("%", "%%"))

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    if not target_url:
        raise ValueError("DATABASE_URL is not configured in .env or alembic.ini")

    context.configure(
        url=target_url,
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
    """Run migrations in 'online' mode with async engine."""
    if not target_url:
        raise ValueError(
            "DATABASE_URL is not set. Please provide your Supabase connection string in .env"
        )

    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = target_url

    connect_args = {}
    if "asyncpg" in target_url:
        connect_args["statement_cache_size"] = 0

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
