# backend/start.py
import sys
import os

# Ensure we can import app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

def main():
    print("🚀 Starting Cyber Law Chatbot...")
    
    try:
        # Import your app
        from app.main import app
        import uvicorn
        
        print("✅ All imports successful!")
        print(f"📚 API Docs: http://localhost:8000/docs")
        print(f"🔗 API: http://localhost:8000")
        
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure you're in the 'backend' directory")
        print("2. Check if app/ folder exists here")
        print("3. Verify app/ has __init__.py file")
        
        # Show directory structure
        print(f"\nCurrent directory: {os.getcwd()}")
        print("Contents:")
        for item in os.listdir('.'):
            print(f"  {'📁' if os.path.isdir(item) else '📄'} {item}")
            
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()