# simple_test.py
import sys
import os

print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# List contents
print("\n📁 Contents of current directory:")
for item in os.listdir('.'):
    print(f"  {'📁' if os.path.isdir(item) else '📄'} {item}")

# Check if app exists
if os.path.exists('app'):
    print("\n✅ app/ folder exists!")
    print("📁 Contents of app/:")
    for item in os.listdir('app'):
        print(f"  {'📁' if os.path.isdir(f'app/{item}') else '📄'} {item}")
else:
    print("\n❌ app/ folder NOT found!")