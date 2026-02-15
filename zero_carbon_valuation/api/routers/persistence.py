"""
持久化API路由
提供项目保存、加载、删除等功能
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
import os
import json
import uuid
from datetime import datetime

from models import (
    ProjectSaveRequest,
    ProjectListResponse,
    MemoryUpdateRequest
)

# 数据目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")
PROJECTS_DIR = os.path.join(DATA_DIR, "projects")

# 确保目录存在
os.makedirs(PROJECTS_DIR, exist_ok=True)

router = APIRouter(prefix="/api/v1/persistence", tags=["Persistence"])


@router.post("/projects")
async def save_project(req: ProjectSaveRequest) -> Dict[str, Any]:
    """
    保存项目

    支持创建新项目或更新现有项目
    """
    try:
        # 生成项目ID
        project_id = req.project_id or str(uuid.uuid4())
        timestamp = datetime.now().isoformat()

        # 构建文件名
        filename = f"{req.project_name}_{timestamp.replace(':', '-')}.json".replace(" ", "_")
        username_dir = os.path.join(PROJECTS_DIR, req.username)
        os.makedirs(username_dir, exist_ok=True)

        # 项目数据
        project_data = {
            "project_id": project_id,
            "project_name": req.project_name,
            "username": req.username,
            "timestamp": timestamp,
            "version": req.version,
            "config": req.config,
            "metadata": req.metadata or {}
        }

        # 保存到文件
        filepath = os.path.join(username_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(project_data, f, ensure_ascii=False, indent=2)

        return {
            "status": "success",
            "project_id": project_id,
            "filename": filename,
            "timestamp": timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get("/projects/{username}", response_model=ProjectListResponse)
async def list_projects(username: str) -> ProjectListResponse:
    """
    获取用户的所有项目列表

    按时间倒序排列
    """
    try:
        username_dir = os.path.join(PROJECTS_DIR, username)
        projects = []

        if os.path.exists(username_dir):
            for filename in os.listdir(username_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(username_dir, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            proj_data = json.load(f)
                            projects.append({
                                "filename": filename,
                                "project_id": proj_data.get("project_id"),
                                "project_name": proj_data.get("project_name"),
                                "timestamp": proj_data.get("timestamp"),
                                "version": proj_data.get("version"),
                                "metadata": proj_data.get("metadata", {}),
                                "data": proj_data.get("config")
                            })
                    except Exception as e:
                        print(f"Error reading {filename}: {e}")
                        continue

        # 按时间倒序
        projects.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return ProjectListResponse(projects=projects)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目列表失败: {str(e)}")


@router.get("/projects/{username}/{project_id}")
async def get_project(username: str, project_id: str) -> Dict[str, Any]:
    """
    获取单个项目的完整数据
    """
    try:
        username_dir = os.path.join(PROJECTS_DIR, username)

        if not os.path.exists(username_dir):
            raise HTTPException(status_code=404, detail="用户目录不存在")

        # 查找项目文件
        for filename in os.listdir(username_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(username_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    proj_data = json.load(f)
                    if proj_data.get("project_id") == project_id:
                        return proj_data

        raise HTTPException(status_code=404, detail="项目不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取项目失败: {str(e)}")


@router.delete("/projects/{username}/{filename}")
async def delete_project(username: str, filename: str) -> Dict[str, Any]:
    """
    删除项目

    注意: 这会永久删除项目文件
    """
    try:
        username_dir = os.path.join(PROJECTS_DIR, username)
        filepath = os.path.join(username_dir, filename)

        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="文件不存在")

        os.remove(filepath)

        return {
            "status": "success",
            "message": "项目已删除",
            "filename": filename
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/memory/{username}")
async def get_global_memory(username: str) -> Dict[str, Any]:
    """
    获取全局记忆数据

    返回用户的偏好、最近项目、学习数据等
    """
    try:
        memory_file = os.path.join(DATA_DIR, f"memory_{username}.json")

        if os.path.exists(memory_file):
            with open(memory_file, "r", encoding="utf-8") as f:
                return json.load(f)

        # 默认记忆数据
        return {
            "lastAccessedProject": None,
            "recentProjects": [],
            "preferences": {
                "defaultRegion": "广东省",
                "defaultBuildingType": "factory",
                "calculationMode": "simple",
                "autoSaveInterval": 300
            },
            "templates": {
                "regionFactors": {}
            },
            "learnings": {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取记忆数据失败: {str(e)}")


@router.post("/memory")
async def update_global_memory(req: MemoryUpdateRequest) -> Dict[str, Any]:
    """
    更新全局记忆数据

    支持增量更新，会合并现有数据
    """
    try:
        memory_file = os.path.join(DATA_DIR, f"memory_{req.username}.json")

        # 读取现有记忆
        existing = {}
        if os.path.exists(memory_file):
            with open(memory_file, "r", encoding="utf-8") as f:
                existing = json.load(f)

        # 合并更新
        merged = {**existing, **req.updates}

        # 保存
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)

        return {
            "status": "success",
            "message": "记忆数据已更新"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新记忆数据失败: {str(e)}")


@router.post("/memory/{username}/recent")
async def add_recent_project(username: str, project_id: str, project_name: str) -> Dict[str, Any]:
    """
    添加项目到最近访问列表

    最多保留10个项目
    """
    try:
        memory_file = os.path.join(DATA_DIR, f"memory_{username}.json")

        # 读取现有记忆
        if os.path.exists(memory_file):
            with open(memory_file, "r", encoding="utf-8") as f:
                memory = json.load(f)
        else:
            memory = {}

        # 更新最近项目
        recent = memory.get("recentProjects", [])
        # 移除已存在的
        recent = [p for p in recent if p.get("id") != project_id]
        # 添加到开头
        recent.insert(0, {"id": project_id, "name": project_name, "timestamp": datetime.now().isoformat()})
        # 保留最多10个
        recent = recent[:10]

        memory["recentProjects"] = recent
        memory["lastAccessedProject"] = project_id

        # 保存
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)

        return {
            "status": "success",
            "recentProjects": recent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新最近项目失败: {str(e)}")
