import json
import os
import hashlib
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PROJECTS_DIR = os.path.join(DATA_DIR, "projects")

def ensure_dirs():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(PROJECTS_DIR):
        os.makedirs(PROJECTS_DIR)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def register_user(username, password):
    users = load_users()
    if username in users:
        return False, "用户名已存在"
    users[username] = hash_password(password)
    save_users(users)
    return True, "注册成功"

def login_user(username, password):
    users = load_users()
    if username in users and users[username] == hash_password(password):
        return True
    return False

def save_project(username, project_name, config_data):
    user_dir = os.path.join(PROJECTS_DIR, username)
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    
    # Use sanitize project name as part of filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{project_name}_{timestamp}.json".replace(" ", "_")
    filepath = os.path.join(user_dir, filename)
    
    data = {
        "project_name": project_name,
        "timestamp": datetime.now().isoformat(),
        "config": config_data
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return True

def list_projects(username):
    user_dir = os.path.join(PROJECTS_DIR, username)
    if not os.path.exists(user_dir):
        return []
    
    projects = []
    if os.path.exists(user_dir):
        for f in os.listdir(user_dir):
            if f.endswith(".json"):
                filepath = os.path.join(user_dir, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as pf:
                        proj_data = json.load(pf)
                        projects.append({
                            "filename": f,
                            "project_name": proj_data.get("project_name", f),
                            "timestamp": proj_data.get("timestamp", ""),
                            "data": proj_data.get("config", {})
                        })
                except:
                    continue
    
    # Sort by timestamp descending
    projects.sort(key=lambda x: x["timestamp"], reverse=True)
    return projects

def delete_project(username, filename):
    filepath = os.path.join(PROJECTS_DIR, username, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False

ensure_dirs()
