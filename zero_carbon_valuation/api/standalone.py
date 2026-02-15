"""
简化版启动脚本 - 用于调试打包问题
"""
import sys
from pathlib import Path

# 添加路径
api_dir = Path(__file__).parent
sys.path.insert(0, str(api_dir))
modules_dir = api_dir.parent / "modules"
if modules_dir.exists():
    sys.path.insert(0, str(modules_dir))

print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"API directory: {api_dir}")
print(f"Modules directory: {modules_dir}")
print(f"sys.path: {sys.path}")

try:
    from fastapi import FastAPI
    print("✓ FastAPI imported")
except Exception as e:
    print(f"✗ FastAPI import failed: {e}")
    sys.exit(1)

try:
    import uvicorn
    print("✓ uvicorn imported")
except Exception as e:
    print(f"✗ uvicorn import failed: {e}")
    sys.exit(1)

try:
    from config import create_app
    print("✓ config imported")
except Exception as e:
    print(f"✗ config import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from routers import calculation, simulation, persistence, export
    print("✓ routers imported")
except Exception as e:
    print(f"✗ routers import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 创建应用
print("\n=== Creating app ===")
app = create_app()

# 注册路由
print("=== Registering routes ===")
app.include_router(calculation.router, prefix="/api/v1")
app.include_router(simulation.router, prefix="/api/v1")
app.include_router(persistence.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "ZeroCarbon Pro", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

print("\n=== Starting server ===")
print("Access: http://localhost:8000/")
print("Docs: http://localhost:8000/docs")
print("=" * 50)

# 启动服务器
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8000,
    reload=False,
    log_level="info"
)
