from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool, text
from alembic import context

# Load our models so Alembic can auto-generate migrations
from app.db.models import Base  # noqa: F401

config = context.config

# Override sqlalchemy.url from DATABASE_URL env var
# Convert async URL to sync for Alembic (asyncpg → psycopg2)
db_url = os.environ["DATABASE_URL"].replace(
    "postgresql+asyncpg://", "postgresql://"
).replace(
    "postgresql+psycopg2://", "postgresql://"
)
config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        # Enable pgvector extension before running migrations
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
