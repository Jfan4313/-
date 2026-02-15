# FastAPI后端服务安装说明

## 依赖安装

### 1. 后端Python依赖

```bash
cd /Users/su/Desktop/code/项目/零碳项目收益分析软件/zero_carbon_valuation/api
pip install -r requirements.txt
```

### 2. 前端依赖

```bash
cd /Users/su/Desktop/code/项目/零碳项目收益评估软件前端
npm install axios idb
```

## 启动服务

### 启动后端服务

```bash
cd /Users/su/Desktop/code/项目/零碳项目收益分析软件/zero_carbon_valuation/api
python main.py
```

后端将在 http://localhost:8000 启动

API文档: http://localhost:8000/docs
ReDoc文档: http://localhost:8000/redoc

### 启动前端服务

```bash
cd /Users/su/Desktop/code/项目/零碳项目收益评估软件前端
npm run dev
```

前端将在 http://localhost:5173 启动

## 环境变量

创建 `.env` 文件在前端项目目录下：

```
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_OFFLINE_MODE=true
VITE_AUTO_SAVE_INTERVAL=300
```

## API端点

### 计算API

- `POST /api/v1/calculation/solar` - 光伏收益计算
- `POST /api/v1/calculation/storage` - 储能套利计算
- `POST /api/v1/calculation/hvac` - 空调节能计算
- `POST /api/v1/calculation/lighting` - 照明节能计算
- `POST /api/v1/calculation/ev` - 充电桩收益计算

### 模拟API

- `POST /api/v1/simulation/8760` - 8760小时完整模拟

### 持久化API

- `POST /api/v1/persistence/projects` - 保存项目
- `GET /api/v1/persistence/projects/{username}` - 获取项目列表
- `GET /api/v1/persistence/projects/{username}/{id}` - 获取单个项目
- `DELETE /api/v1/persistence/projects/{username}/{filename}` - 删除项目
- `GET /api/v1/persistence/memory/{username}` - 获取全局记忆
- `POST /api/v1/persistence/memory` - 更新全局记忆

### 导出API

- `POST /api/v1/export/project/json` - 导出JSON
- `POST /api/v1/export/project/excel` - 导出Excel
