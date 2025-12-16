# verify_setup_fixed.py
import os
import sys

print("=== SETUP VERIFICATION ===\n")

# 1. Check folder
print("1. Current directory:", os.getcwd())
print("   ✅ Correct folder" if "cybot-gov" in os.getcwd() and "clean" not in os.getcwd() else "   ⚠️ Check folder name")

# 2. Check git
print("\n2. Checking Git connection...")
try:
    import subprocess
    result = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True, cwd=os.getcwd())
    if "noctxrne/cybot-gov" in result.stdout:
        print("   ✅ Git connected to correct GitHub repository")
    else:
        print("   ⚠️ Git not connected or wrong remote")
except Exception as e:
    print(f"   ⚠️ Git check failed: {e}")

# 3. Check venv
venv_path = os.path.join(os.getcwd(), "venv")
if os.path.exists(venv_path):
    print("3. ✅ Virtual environment exists")
else:
    print("3. ❌ No venv folder found")

# 4. Check key files
print("\n4. Checking key files:")
required_files = [
    "app/__init__.py",
    "app/config.py", 
    "app/main.py",
    "app/database/__init__.py",
    "app/database/session.py",
    "app/services/__init__.py",
    "requirements.txt",
    ".gitignore"
]

for file in required_files:
    file_path = os.path.join(os.getcwd(), file.replace('/', '\\'))
    if os.path.exists(file_path):
        print(f"   ✅ {file}")
    else:
        print(f"   ❌ {file} (missing)")

# 5. Test imports
print("\n5. Testing Python imports...")
try:
    # Add current directory to path
    sys.path.insert(0, os.getcwd())
    
    from app.config import settings
    print(f"   ✅ Config loaded: {settings.DATABASE_URL[:50]}...")
    
    from app.database.session import engine, Base
    print("   ✅ Database engine imported")
    
    from app.main import app
    print(f"   ✅ FastAPI app loaded: {app.title}")
    
    print("\n🎉 All imports successful! Ready to run.")
    
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    print("\nChecking Python path and structure...")
    
    # Show Python path
    print(f"\nPython path:")
    for i, path in enumerate(sys.path[:5]):
        print(f"  {i}. {path}")
    
    # Show app directory contents
    app_dir = os.path.join(os.getcwd(), "app")
    if os.path.exists(app_dir):
        print(f"\nContents of {app_dir}:")
        for item in os.listdir(app_dir):
            full_path = os.path.join(app_dir, item)
            if os.path.isdir(full_path):
                print(f"  📁 {item}/")
            else:
                print(f"  📄 {item}")
    else:
        print(f"\n❌ {app_dir} doesn't exist!")

print("\n=== VERIFICATION COMPLETE ===")