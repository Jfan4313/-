"""
最简单的测试服务器
"""
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Test Server")

@app.get("/")
async def root():
    return {"message": "Test server is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    print("Starting test server on http://localhost:8000/")
    uvicorn.run(app, host="0.0.0.0", port=8000)
