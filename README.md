# Live Stream Clip Agent

直播切片 Agent 工程版项目。系统把直播录制或长视频转成可审核、可导出的短视频运营资产，覆盖视频入库、ASR 转写、候选切片识别、LangChain 结构化文案生成、人工审核和发布清单导出。

## 技术栈

- 后端：FastAPI、SQLAlchemy、Redis/RQ、ffmpeg、LangChain。
- 前端：Vue 3、Vite、TypeScript、Element Plus、Vue Router，多目录管理台结构，使用 `fetch` 请求相对 `/api`，由 Vite proxy 转发后端。
- 数据库：本地 Docker PostgreSQL，新建数据库 `live-stream-clip-agent`。
- 存储：本地文件存储，预留 MinIO 适配。

## 表结构初始化

项目不使用 Alembic。建表 SQL 统一放在：

```text
backend/app/db/init_sql.py
```

FastAPI 启动时会调用 `init_database()`，自动执行 `CREATE TABLE IF NOT EXISTS`。`backend/app/models/tables.py` 是 SQLAlchemy ORM 映射，用来让业务代码用 Python 类读写这些表，不是迁移文件。

## 后端虚拟环境

后端使用本机既有 `uv` 创建 `.venv`：

```powershell
cd backend
D:\uv\uv.exe venv --python 3.11 .venv
D:\uv\uv.exe pip install -r requirements.txt
```

当前 `.venv` 使用 CPython 3.11。

## 本地数据库

建库 SQL 放在：

```text
backend/scripts/create_database.sql
```

```sql
CREATE DATABASE "live-stream-clip-agent";
```

默认连接：

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/live-stream-clip-agent
```

如需查看当前建表 SQL：

```powershell
cd backend
python scripts/init_db.py
```

## 本地启动

后端 API：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

RQ worker：

```powershell
cd backend
.\.venv\Scripts\python.exe scripts/run_worker.py
```

开发环境默认启动 1 个 worker，任务会按顺序消费 `video_ops` 队列。硬件资源和模型额度足够时，可以在多个终端重复执行同一条 worker 命令来提高并发。

前端：

```powershell
cd frontend
pnpm dev
```

## 文档

完整技术文档见 `docs/technical-design.md`。

未完成事项清单见 `docs/remaining-work.md`，完成一项后直接删除对应条目。
