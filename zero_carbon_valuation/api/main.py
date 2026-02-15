"""
FastAPI后端服务主应用
零碳项目收益评估软件
"""
import sys
from pathlib import Path

# 添加当前目录到Python路径（支持PyInstaller打包后的执行）
if getattr(sys, 'frozen', False):
    # PyInstaller打包后的环境
    meipass = Path(sys._MEIPASS)
    # 数据文件直接复制到meipass目录下
    sys.path.insert(0, str(meipass))  # 添加根目录
    sys.path.insert(0, str(meipass / "api"))  # 添加api目录
    sys.path.insert(0, str(meipass / "modules"))  # 添加modules目录
else:
    # 开发环境
    sys.path.insert(0, str(Path(__file__).parent))
    sys.path.insert(0, str(Path(__file__).parent.parent / "modules"))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager

from config import create_app
from routers import calculation, simulation, persistence, export


# 获取静态文件目录
STATIC_DIR = Path(__file__).parent / "static"
if not STATIC_DIR.exists():
    if getattr(sys, 'frozen', False):
        STATIC_DIR = Path(sys._MEIPASS) / "api" / "static"
    else:
        STATIC_DIR = Path(__file__).parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("=== 零碳项目收益评估API服务启动 ===")
    print("访问文档: http://localhost:8000/docs")
    print("访问应用: http://localhost:8000/")
    yield
    print("=== 零碳项目收益评估API服务关闭 ===")


# 创建应用
app = create_app()
app.router.lifespan_context = lifespan


# 健康检查端点 - 必须最早定义
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "static_dir": str(STATIC_DIR), "static_exists": STATIC_DIR.exists()}


# 注册API路由
app.include_router(calculation.router)
app.include_router(simulation.router)
app.include_router(persistence.router)
app.include_router(export.router)


# 挂载静态文件和根路径（在health之后，API路由之后）
if STATIC_DIR.exists():
    # 挂载assets目录到/assets路径
    if (STATIC_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")
    # 挂载整个static目录到根路径（html=True会自动返回index.html）
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "message": "零碳项目收益评估API",
            "version": "1.0.0",
            "docs": "/docs",
            "redoc": "/redoc",
            "note": "Frontend not built. Run build_frontend.py first."
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
