from sqlalchemy.orm import sessionmaker, scoped_session
from .engine import create_engine_from_config

def create_session_factory(engine=None):
    if engine is None:
        engine = create_engine_from_config()
    
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return session_factory

def create_scoped_session(session_factory):
    return scoped_session(session_factory)
