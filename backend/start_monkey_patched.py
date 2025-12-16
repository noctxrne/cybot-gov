# start_monkey_patched.py
import sys

# MONKEY PATCH AT SYSTEM LEVEL - before ANY imports
import types

# Create fake huggingface_hub module
class FakeHuggingFaceHub(types.ModuleType):
    def __init__(self):
        # Import real module
        import huggingface_hub as real
        super().__init__('huggingface_hub')
        
        # Copy everything
        for attr in dir(real):
            if not attr.startswith('_'):
                setattr(self, attr, getattr(real, attr))
        
        # Add cached_download alias
        if hasattr(real, 'hf_hub_download'):
            self.cached_download = real.hf_hub_download
        else:
            # Create dummy function
            def dummy(*args, **kwargs):
                raise ImportError("cached_download not available")
            self.cached_download = dummy

# Replace in sys.modules BEFORE any imports
sys.modules['huggingface_hub'] = FakeHuggingFaceHub()

print("✅ Monkey patch applied at system level")

# Now import your app
from app.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Cyber Law Chatbot Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)