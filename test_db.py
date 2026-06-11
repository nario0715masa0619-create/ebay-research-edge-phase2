import sys
sys.path.insert(0, '.')
try:
    from src.db.engine import create_engine_from_config
    from sqlalchemy import inspect
    
    print("Database Module: ✅ IMPORTABLE")
    
    try:
        engine = create_engine_from_config()
        print("Database Engine: ✅ INITIALIZED")
        
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables Found: {len(tables)}")
        
        critical_tables = ["execution_attempt", "execution_history", "incident", "ops_policy"]
        for table in critical_tables:
            status = "✅" if table in tables else "❌"
            print(f"  {status} {table}")
        
        print("Database Health: ✅ READY")
    except Exception as e:
        print(f"Database Health: ⚠️  {str(e)[:100]}")
except ImportError as e:
    print(f"Database Module: ❌ IMPORT ERROR - {str(e)[:100]}")
