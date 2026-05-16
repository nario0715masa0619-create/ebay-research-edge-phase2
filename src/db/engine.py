from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from .config import DatabaseConfig

def create_engine_from_config(database_url: str = DatabaseConfig.DATABASE_URL, echo: bool = DatabaseConfig.DB_ECHO):
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["timeout"] = DatabaseConfig.DB_BUSY_TIMEOUT_MS / 1000.0
        
    engine = create_engine(
        database_url,
        echo=echo,
        connect_args=connect_args if connect_args else {},
        pool_pre_ping=True
    )

    if database_url.startswith("sqlite"):
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            if DatabaseConfig.DB_ENABLE_FOREIGN_KEYS:
                cursor.execute("PRAGMA foreign_keys=ON")
            if DatabaseConfig.DB_ENABLE_WAL:
                cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return engine
