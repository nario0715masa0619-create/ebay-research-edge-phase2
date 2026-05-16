import os

class DatabaseConfig:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ebay_research.db")
    DB_ECHO = os.getenv("DB_ECHO", "false").lower() == "true"
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_BUSY_TIMEOUT_MS = int(os.getenv("DB_BUSY_TIMEOUT_MS", "30000"))
    DB_ENABLE_WAL = os.getenv("DB_ENABLE_WAL", "true").lower() == "true"
    DB_ENABLE_FOREIGN_KEYS = os.getenv("DB_ENABLE_FOREIGN_KEYS", "true").lower() == "true"
    ALEMBIC_AUTO_UPGRADE_ON_BOOT = os.getenv("ALEMBIC_AUTO_UPGRADE_ON_BOOT", "false").lower() == "true"
    REPOSITORY_BACKEND = os.getenv("REPOSITORY_BACKEND", "sqlite") # memory, sqlite, postgresql
