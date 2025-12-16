# test.py - CORRECTED VERSION
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")

try:
    # Now this should work
    from app.config import settings
    print(f"✅ Config loaded: {settings.DATABASE_URL[:50]}...")
    
    # Test other imports
    from app.database.session import engine, Base
    print("✅ Database components imported")
    
    # Create tables (for SQLite testing)
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    # Test RAG service
    from app.services.rag_service import HybridRAGService
    rag = HybridRAGService(settings)
    print("✅ RAG service initialized")
    
    # Test query
    response = rag.query("What is hacking?")
    print(f"✅ Test query response: {response['intent']}")
    
    print("\n🎉 All tests passed! Your chatbot is ready.")
    
except ModuleNotFoundError as e:
    print(f"❌ Module not found: {e}")
    print("\nChecking module structure...")
    
    # Show what's available
    import pkgutil
    if 'app' in [name for _, name, _ in pkgutil.iter_modules()]:
        print("✅ 'app' package is importable")
        import app
        print(f"App contents: {dir(app)}")
    else:
        print("❌ 'app' package not found in Python path")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()