import pytest
import os
from sqlalchemy import create_engine, inspect
from src.db.bootstrap import bootstrap_database
from src.db.config import DatabaseConfig

def test_bootstrap_creates_tables():
    # Use a specific file for this test to verify persistence
    db_file = "bootstrap_test.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    original_url = DatabaseConfig.DATABASE_URL
    DatabaseConfig.DATABASE_URL = f"sqlite:///{db_file}"
    
    try:
        # Run bootstrap
        bootstrap_database(auto_upgrade=False)
        
        engine = create_engine(DatabaseConfig.DATABASE_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"Tables found: {tables}")
        
        expected_tables = {
            "source_items", 
            "product_candidates", 
            "candidate_evidences", 
            "ebay_listings", 
            "monitoring_events", 
            "job_runs"
        }
        for table in expected_tables:
            assert table in tables
            
        engine.dispose()
            
    finally:
        DatabaseConfig.DATABASE_URL = original_url
        try:
            if os.path.exists(db_file):
                os.remove(db_file)
        except:
            pass

def test_sqlite_pragma_application():
    # Verify WAL and Foreign Keys
    db_file = "pragma_test.db"
    if os.path.exists(db_file):
        os.remove(db_file)
        
    original_url = DatabaseConfig.DATABASE_URL
    DatabaseConfig.DATABASE_URL = f"sqlite:///{db_file}"
    
    try:
        bootstrap_database()
        engine = create_engine(DatabaseConfig.DATABASE_URL)
        
        with engine.connect() as conn:
            # Check foreign keys
            fk_res = conn.exec_driver_sql("PRAGMA foreign_keys").scalar()
            assert fk_res == 1
            
            # Check journal mode
            jm_res = conn.exec_driver_sql("PRAGMA journal_mode").scalar()
            assert jm_res.lower() == "wal"
        
        engine.dispose()
            
    finally:
        DatabaseConfig.DATABASE_URL = original_url
        try:
            if os.path.exists(db_file):
                os.remove(db_file)
        except:
            pass
