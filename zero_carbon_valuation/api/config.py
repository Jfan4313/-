"""
FastAPI配置和CORS设置
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    app = FastAPI(
        title="零碳项目收益评估API",
        description="提供零碳项目收益评估的核心计算服务",
        version="1.0.0"
    )

    # CORS配置 - 打包后前端和后端同源，但保留开发环境支持
    origins = [
        "*",  # 允许所有源（打包后同源访问）
        "http://localhost:5173",  # Vite开发服务器
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


def get_origins() -> List[str]:
    """获取允许的源地址"""
    return [
        "*",  # 打包后前端和后端同源
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ]
