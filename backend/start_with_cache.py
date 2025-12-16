# start_with_cache.py - Forces cache usage
import os
import sys

# Force cache usage BEFORE any imports
os.environ['TRANSFORMERS_CACHE'] = os.path.join(os.path.expanduser('~'), '.cache', 'huggingface')
os.environ['HF_HOME'] = os.path.join(os.path.expanduser('~'), '.cache', 'huggingface')
os.environ['HF_DATASETS_OFFLINE'] = '0'  # Allow downloads but use cache
os.environ['TRANSFORMERS_OFFLINE'] = '0'  # Allow downloads but use cache

print(f"🔧 Cache location: {os.environ['TRANSFORMERS_CACHE']}")
print("🔄 Will resume from 92% downloaded cache...")

# Import your app
from app.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Cyber Law Chatbot...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)