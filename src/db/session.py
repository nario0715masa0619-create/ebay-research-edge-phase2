from sqlalchemy.orm import sessionmaker, scoped_session
from .engine import create_engine_from_config
from contextlib import contextmanager

def create_session_factory(engine=None):
    if engine is None:
        engine = create_engine_from_config()
    
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return session_factory

def create_scoped_session(session_factory):
    return scoped_session(session_factory)

class SessionManager:
    def __init__(self, engine=None):
        self.session_factory = create_session_factory(engine)
    
    @contextmanager
    def session(self):
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session(self):
        return self.session_factory()
