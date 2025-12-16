# test.py - Complete test file
import os
import sys

# Add current directory to path (helps with imports)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🧪 Testing Cyber Law Chatbot Components...")
print("=" * 50)

try:
    # 1. Test config import
    from app.config import settings
    print("✅ Config loaded successfully")
    print(f"   Model: {settings.EMBEDDING_MODEL}")
    print(f"   Database: {settings.DATABASE_URL[:30]}...")
    
    # 2. Test PDFProcessor import and creation
    from app.services.pdf_processor import PDFProcessor
    processor = PDFProcessor(settings)
    print("✅ PDFProcessor created successfully!")
    print(f"   Vector store path: {settings.VECTOR_STORE_PATH}")
    
    # 3. Test embedding model
    test_text = "Cyber security law protects digital assets"
    embedding = processor.embedding_model.encode([test_text])
    print(f"✅ Embedding model working (shape: {embedding.shape})")
    
    # 4. Test LanceDB vector store
    from app.services.vector_store import VectorStoreManager
    vector_store = VectorStoreManager(
        db_path=os.path.join(settings.VECTOR_STORE_PATH, "lancedb"),
        table_name="test_table"
    )
    print("✅ LanceDB VectorStoreManager created")
    
    # 5. Test RAG service
    from app.services.rag_service import HybridRAGService
    rag = HybridRAGService(settings)
    print("✅ HybridRAGService created")
    
    print("\n" + "=" * 50)
    print("🎉 ALL COMPONENTS WORKING!")
    print("\nYour chatbot is ready for:")
    print("1. Frontend: http://localhost:3000")
    print("2. Admin: http://localhost:3000/admin")
    print("3. API: http://localhost:8000")
    
except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    print("\nPossible fixes:")
    print("1. Make sure you're in 'backend' folder")
    print("2. Check if venv is activated (should see '(venv)' in prompt)")
    print("3. Check if __init__.py files exist in app/ and app/services/")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\nTroubleshooting:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Install LanceDB: pip install lancedb pandas")
    print("3. Check .env file exists with correct settings")