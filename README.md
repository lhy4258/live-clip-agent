# Live Stream Clip Agent

直播切片 Agent 工程版项目。系统把直播录制或本地长视频转成可审核、可导出的短视频运营资产，覆盖视频入库、ASR 转写、候选切片识别、LangChain 文案生成、人工审核、ffmpeg 异步导出和发布清单导出。

## 技术栈

- 后端：FastAPI、SQLAlchemy、PostgreSQL、Redis/RQ、LangChain、ffmpeg-python。
- 前端：Vue 3、Vite、TypeScript、Element Plus、Vue Router。
- 数据库：本地 Docker PostgreSQL，数据库名 `live-stream-clip-agent`。
- 队列：Redis + RQ，默认队列名 `video_ops`。
- ASR：默认 mock，可切换为阿里百炼 `qwen3-asr-flash`。
- ffmpeg：默认为空，需本地进行配置
- 存储：本地文件存储 `backend/data/files`，预留 MinIO 扩展。



## 环境配置

后端所有资源配置都从 `backend/.env` 读取。第一次运行时复制模板：

```powershell
cd C:\Users\你的用户名\Desktop\working\demo3\backend
Copy-Item .env.example .env
```

然后根据本机情况修改 `backend/.env`。

核心配置项：

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/live-stream-clip-agent
REDIS_URL=redis://localhost:6379/0
STORAGE_DIR=data/files
LLM_MOCK=true
ASR_PROVIDER=mock
FFMPEG_PATH=
FFPROBE_PATH=
```

说明：

- `DATABASE_URL`：PostgreSQL 连接地址，需要数据库已存在。
- `REDIS_URL`：Redis 连接地址，RQ worker 从 Redis 队列取任务。
- `STORAGE_DIR`：相对 `backend` 目录的本地文件存储路径。
- `LLM_MOCK=true`：本地演示时不调用真实大模型。
- `ASR_PROVIDER=mock`：本地演示时不调用真实 ASR。
- `FFMPEG_PATH`、`FFPROBE_PATH`：如果不想配置系统环境变量，就填写本机 `ffmpeg.exe` 和 `ffprobe.exe` 的绝对路径。

## ffmpeg 配置

本项目不会把 ffmpeg 二进制文件提交到仓库。新机器需要自行准备 ffmpeg。

推荐本地放置方式：

```text
C:\Users\你的用户名\Desktop\working\demo3\tools\ffmpeg\bin\ffmpeg.exe
C:\Users\你的用户名\Desktop\working\demo3\tools\ffmpeg\bin\ffprobe.exe
```

然后在 `backend/.env` 中配置：

```env
FFMPEG_PATH=C:\Users\你的用户名\Desktop\working\demo3\tools\ffmpeg\bin\ffmpeg.exe
FFPROBE_PATH=C:\Users\你的用户名\Desktop\working\demo3\tools\ffmpeg\bin\ffprobe.exe
```

也可以把 ffmpeg 加入系统 `PATH`，这时 `FFMPEG_PATH` 和 `FFPROBE_PATH` 可以留空。

ffmpeg 在项目中的作用：

- 从视频中抽取音频，供真实 ASR 使用。
- 根据候选切片的开始/结束时间导出短视频文件。

## ASR 配置

默认配置：

```env
ASR_PROVIDER=mock
ASR_MODEL=qwen3-asr-flash
ASR_API_KEY=
```

`mock` 模式不调用外部服务，会生成演示转写文本，适合本地开发和前端联调。

使用阿里百炼 `qwen3-asr-flash` 时修改为：

```env
ASR_PROVIDER=aliyun_qwen3_asr_flash
ASR_MODEL=qwen3-asr-flash
ASR_API_KEY=你的DashScope或百炼APIKey
ASR_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions
ASR_MAX_DURATION_SEC=300
ASR_MAX_PAYLOAD_BYTES=10485760
```

注意：

- 当前实现按单段音频不超过 5 分钟设计，即 `ASR_MAX_DURATION_SEC=300`。
- 真实 ASR 流程是：本地视频 -> ffmpeg 抽取 mp3 音频 -> Base64 Data URL -> `qwen3-asr-flash` 转文字。
- ffmpeg 不负责转文字，ASR 模型才负责转写。
- `ASR_MODEL` 只表示模型名，不会自动启用真实 ASR；是否调用真实模型由 `ASR_PROVIDER` 决定。

## 数据库初始化

项目不使用 Alembic。建表 SQL 统一放在：

```text
backend/app/db/init_sql.py
```

FastAPI 启动时会调用 `init_database()`，自动执行 `CREATE TABLE IF NOT EXISTS`。

建库 SQL：

```text
backend/scripts/create_database.sql
```

内容：

```sql
CREATE DATABASE "live-stream-clip-agent";
```

如果数据库还不存在，可以在本地 PostgreSQL 中先执行这条 SQL。

`backend/app/models/tables.py` 是 SQLAlchemy ORM 映射，用来让业务代码用 Python 类读写数据表，不是迁移文件。

## 安装依赖

后端使用本项目自己的 `.venv`，不要使用系统全局 Python 运行后端：

```powershell
cd C:\Users\你的用户名\Desktop\working\demo3\backend
D:\uv\uv.exe venv --python 3.11 .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

如果本机 `uv` 路径不同，把 `D:\uv\uv.exe` 替换成自己的 `uv` 路径。

前端：

```powershell
cd C:\Users\你的用户名\Desktop\working\demo3\frontend
pnpm install
```

## 本地启动

启动后端 API：

```powershell
cd C:\Users\你的用户名\Desktop\working\demo3\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

启动 RQ worker：

```powershell
cd C:\Users\你的用户名\Desktop\working\demo3\backend
.\.venv\Scripts\python.exe scripts/run_worker.py
```

开发环境默认启动 1 个 worker 即可。硬件资源和模型额度足够时，可以在多个终端重复执行 worker 命令，让多个 worker 共同消费 `video_ops` 队列。

启动前端：

```powershell
cd C:\Users\你的用户名\Desktop\working\demo3\frontend
pnpm dev
```

前端访问：

```text
http://127.0.0.1:5173
```

前端代码只请求相对地址 `/api/v1/video-ops/...`，Vite proxy 会把 `/api` 转发到 `http://127.0.0.1:8000`，因此前端不需要 `.env`。

## 演示数据

如需填充测试数据：

```powershell
cd C:\Users\你的用户名\Desktop\working\demo3\backend
.\.venv\Scripts\python.exe scripts/seed_demo_data.py
```

## 测试

后端测试：

```powershell
cd C:\Users\你的用户名\Desktop\working\demo3\backend
.\.venv\Scripts\python.exe -m pytest tests
```

## 文档

完整技术文档：

```text
docs/technical-design.md
```

未完成事项清单：

```text
docs/remaining-work.md
```

完成一项后，直接删除 `docs/remaining-work.md` 中对应条目。
