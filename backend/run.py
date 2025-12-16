import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Cyber Law Chatbot Backend...")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔗 API: http://localhost:8000")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )