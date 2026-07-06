# 直播切片 Agent 技术文档

## 1. 项目目标

直播切片 Agent 用于把直播录制或长视频转成可运营的短视频素材。系统完成视频入库、音频转写、候选切片识别、运营文案生成、人工审核、短视频文件导出和发布清单导出。

面试讲法重点：

- 这是一个多模态内容流水线，不是简单文案生成器。
- ffmpeg、ASR、数据库写入、时间边界校验负责确定性处理。
- LangChain 用于候选片段识别、语义评分、标题简介标签生成、风险审核这类判断和生成任务。
- 后端采用单 Agent 多 Tool 架构：`LiveClipAgent` 负责流程编排，普通 Tool 负责确定性动作，Chain Tool 负责大模型语义任务。
- 人工审核保留最终控制权，系统不自动发布到平台。

## 2. 技术栈

后端：

- Python 3.11+
- FastAPI
- Pydantic
- SQLAlchemy
- Redis/RQ
- ffmpeg-python
- LangChain
- OpenAI-compatible LLM

前端：

- Vue 3
- Vite
- TypeScript
- Element Plus
- Vue Router

数据：

- 本地 Docker PostgreSQL
- 数据库名：`live-stream-clip-agent`
- 本地文件存储：`data/files`
- 预留 MinIO 扩展

## 3. 本地数据库

本项目使用已经启动的本地 Docker PostgreSQL，不在项目内重复创建 PostgreSQL 容器。

建库 SQL：

```sql
CREATE DATABASE "live-stream-clip-agent";
```

默认 `.env`：

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/live-stream-clip-agent
REDIS_URL=redis://localhost:6379/0
STORAGE_DIR=data/files
API_KEY=dev-live-stream-clip-agent
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=gpt-4.1-mini
LLM_MOCK=true
LANGSMITH_TRACING=false
FRONTEND_ORIGIN=http://localhost:5173
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

数据库只允许后端访问，前端不直连数据库。

## 4. 总体架构

```mermaid
flowchart LR
  UI["Vue + Vite 管理台"] --> API["FastAPI /api/v1/video-ops"]
  API --> DB["PostgreSQL live-stream-clip-agent"]
  API --> RQ["Redis/RQ 异步任务"]
  RQ --> Agent["LiveClipAgent"]
  Agent --> ASR["ASR Tool"]
  Agent --> Tools["普通 Tools"]
  Agent --> LC["Chain Tools"]
  ASR --> DB
  LC --> LLM["OpenAI-compatible LLM 或 mock"]
  LC --> DB
  Tools --> DB
  API --> Export["CSV/JSON 导出"]
  RQ --> FFmpeg["ffmpeg 视频切片导出"]
  FFmpeg --> Storage["data/files/clips"]
```

核心流程：

1. 运营人员在前端登记视频路径或上传视频。
2. 后端记录 `source_videos`。
3. 转写任务读取视频，提取音频并生成 `transcript_segments`。
4. `LiveClipAgent` 调用 `detect_candidates_tool`，由 `CandidateDetectionChain` 从转写时间轴中选择候选片段。
5. 普通代码校验候选片段时间范围、文本范围和重叠情况，防止模型编造不存在的时间段。
6. `LiveClipAgent` 继续调用评分、运营文案和风险审核 Chain Tool。
7. `save_clip_tool` 保存候选切片记录。
8. 人工审核确认或拒绝切片。
9. 确认后的切片可创建异步导出任务，由 RQ worker 调用 ffmpeg 切出短视频文件。
10. 确认后的切片生成 `publish_plans`。
11. 前端导出 CSV 或 JSON 发布清单。

## 5. LangChain 使用边界

使用 LangChain 的地方：

- `CandidateDetectionChain`：从带时间戳的转写片段中选择候选切片时间段，输出 `start_sec`、`end_sec`、`reason`、`highlight`、`confidence`。
- `ClipScoringChain`：判断 hook、value_point、audience、semantic_score。
- `PublishCopyChain`：生成标题、简介、标签、封面文案。
- `RiskReviewChain`：辅助判断夸大承诺、敏感表达、合规风险。

不使用 LangChain 的地方：

- API 路由。
- 状态码处理。
- 数据库事务。
- 任务重试。
- 文件路径判断。
- CSV/JSON 导出。
- ffmpeg 视频切片导出。
- Agent 固定流程编排、工具调用顺序、任务状态回写。
- 候选片段时间边界校验、去重和数据库保存。

原因：这些逻辑是确定性业务规则，代码比模型更可靠、可测试、可审计。

## 6. 后端模块

目录：

```text
backend/
  app/
    agents/
      live_clip_agent.py
    api/
      deps.py
      v1/
        videos.py
        jobs.py
        clips.py
        publish_plans.py
        chain_runs.py
    chains/
      schemas.py
      candidate_detection.py
      clip_scoring.py
      publish_copy.py
      risk_review.py
    core/
      config.py
      database.py
      logging.py
      security.py
    db/
      init_sql.py
    jobs/
      pipeline.py
    models/
      tables.py
    schemas/
      video_ops.py
    services/
      agent_pipeline.py
      clip_detection.py
      exporter.py
      queue.py
      risk_rules.py
      storage.py
      tasks.py
      transcription.py
    tools/
      transcription_tool.py
      candidate_detection_tool.py
      clip_scoring_tool.py
      publish_copy_tool.py
      risk_review_tool.py
      save_clip_tool.py
      export_clip_video_tool.py
    main.py
```

职责：

- `api`：参数校验、鉴权、调用 service。
- `agents`：`LiveClipAgent` 单 Agent 编排入口。
- `tools`：Agent 可调用能力，分为普通 Tool 和 Chain Tool。
- `services`：确定性业务逻辑。
- `chains`：LangChain 结构化输入输出。
- `db/init_sql.py`：唯一建表 SQL 来源，使用 `CREATE TABLE IF NOT EXISTS`。
- `jobs`：长任务入口。
- `models/tables.py`：SQLAlchemy ORM 映射，让业务代码用 Python 类读写数据库表，不负责建表迁移。
- `schemas`：REST DTO。
- `core/database.py`：数据库 engine、SessionLocal、get_db、启动建表入口。
- `core`：配置、数据库、安全、日志。

本项目不使用 Alembic。原因是作品集 demo 更重视可读、可直接运行和与 DBX 配合调试。表结构初始化采用与前序项目一致的显式 SQL 方案。

表结构来源：

```text
backend/app/db/init_sql.py
```

建库 SQL 来源：

```text
backend/scripts/create_database.sql
```

启动行为：

```text
FastAPI startup -> init_database() -> build_init_sql() -> CREATE TABLE IF NOT EXISTS
```

DBX 的角色：

- 查看表结构。
- 手动检查数据。
- 必要时执行 SQL 调试。

代码里的 `init_sql.py` 仍然必须保留，因为它是新库自动建表和他人复现项目结构的来源。

## 7. 数据表

### source_videos

记录直播录制或长视频。

字段：

- `id`
- `title`
- `file_uri`
- `duration_sec`
- `source`
- `license`
- `status`
- `created_at`
- `updated_at`

### transcript_segments

记录带时间戳的 ASR 转写片段。

字段：

- `id`
- `video_id`
- `start_sec`
- `end_sec`
- `text`
- `confidence`

### video_clips

记录候选或已审核切片。

字段：

- `id`
- `video_id`
- `start_sec`
- `end_sec`
- `title`
- `summary`
- `tags`
- `cover_text`
- `score`
- `status`
- `risk_level`
- `export_status`
- `clip_file_uri`
- `export_error`
- `exported_at`

### clip_reviews

记录人工审核。

字段：

- `id`
- `clip_id`
- `label`
- `reason`
- `reviewer`
- `created_at`

### publish_plans

记录发布清单草稿。

字段：

- `id`
- `clip_id`
- `platform`
- `title`
- `description`
- `hashtags`
- `status`

### agent_tasks

记录异步任务状态。

字段：

- `id`
- `task_type`
- `status`
- `input_json`
- `output_json`
- `error`
- `error_json`
- `trace_id`

### ai_call_logs

记录 AI 调用摘要。

字段：

- `request_id`
- `model`
- `prompt_version`
- `input_hash`
- `latency_ms`
- `token_in`
- `token_out`
- `cost_estimate`
- `error`

### chain_runs

记录 LangChain 调用链。候选片段识别、片段评分、发布文案、风险审核都会写入该表，便于按 `trace_id` 查看一次任务的完整模型调用路径。

字段：

- `id`
- `clip_id`
- `chain_name`
- `prompt_version`
- `model`
- `input_json`
- `output_json`
- `latency_ms`
- `error`
- `trace_id`

## 8. REST API

所有接口前缀为 `/api/v1`，请求需要 `X-API-Key`。

### 视频

`POST /api/v1/video-ops/videos`

请求：

```json
{
  "title": "7月直播复盘",
  "file_uri": "data/files/live-demo.mp4",
  "duration_sec": 900,
  "source": "self_recorded",
  "license": "self_owned"
}
```

`POST /api/v1/video-ops/videos/upload`

上传本地视频文件并创建视频记录，使用 `multipart/form-data`。

表单字段：

- `file`：视频文件，只接受 `video/*`。
- `title`：视频标题。
- `source`：来源，默认 `self_recorded`。
- `license`：授权，默认 `self_owned`。
- `duration_sec`：可选时长。

上传文件保存到 `STORAGE_DIR`，返回创建后的 `source_videos` 记录。

`GET /api/v1/video-ops/videos`

返回视频列表。

`GET /api/v1/video-ops/videos/{id}`

返回视频详情。

`GET /api/v1/video-ops/videos/{id}/transcripts`

返回转写时间轴。

### 任务

`POST /api/v1/video-ops/videos/{id}/transcribe`

创建转写任务。

`POST /api/v1/video-ops/videos/{id}/detect-clips`

创建候选切片任务。

`GET /api/v1/video-ops/jobs/{job_id}`

查询任务状态。

`POST /api/v1/video-ops/jobs/{job_id}/retry`

失败任务手动重新入队。系统不自动重试，避免大模型调用进入循环消耗。

`DELETE /api/v1/video-ops/jobs/{job_id}`

手动删除失败任务记录。只允许删除 `failed` 状态任务，不删除视频、转写、切片或发布清单数据。

### 切片

`GET /api/v1/video-ops/clips`

支持 `status_filter` 查询参数。

`GET /api/v1/video-ops/clips/{id}`

返回切片详情。

`POST /api/v1/video-ops/clips/{id}/review`

请求：

```json
{
  "label": "approved",
  "reason": "内容可用",
  "reviewer": "operator"
}
```

`POST /api/v1/video-ops/clips/{id}/publish-plan`

请求：

```json
{
  "platform": "douyin"
}
```

`POST /api/v1/video-ops/clips/{id}/export`

人工审核通过后创建异步视频导出任务。接口返回 `agent_tasks` 任务记录，真正的 ffmpeg 导出由 RQ worker 执行。

限制：

- 只有 `status=approved` 的切片可以导出。
- 同一个切片在 `export_status=pending/exporting` 时不能重复入队。
- 失败后 `export_status=failed`，可以再次手动发起导出。

导出状态：

- `not_started`：未导出。
- `pending`：已进入队列。
- `exporting`：worker 正在导出。
- `exported`：已生成短视频文件，路径写入 `clip_file_uri`。
- `failed`：导出失败，原因写入 `export_error`，结构化失败原因写入对应任务的 `error_json`。

### 导出

`GET /api/v1/video-ops/publish-plans/export?format=csv`

`GET /api/v1/video-ops/publish-plans/export?format=json`

### LangChain 观测

`GET /api/v1/video-ops/chain-runs`

可选 `trace_id` 过滤。

## 9. 前端设计

前端使用 Vue 3 + Vite + TypeScript + Element Plus + Vue Router。前端恢复为多目录管理台结构：`App.vue` 只负责整体布局、顶栏、侧栏和 `RouterView`，页面内容拆到 `views`，公共布局拆到 `components`，共享业务状态和动作放到 `composables`。

源码结构：

```text
frontend/
  src/
    components/
      AppHeader.vue
      AppSidebar.vue
    composables/
      useVideoOps.ts
      videoOpsContext.ts
    router/
      index.ts
    utils/
      format.ts
    views/
      VideoLibraryView.vue
      ClipReviewView.vue
      PublishListView.vue
      JobMonitorView.vue
      ChainRunsView.vue
    App.vue
    api.ts
    main.ts
    styles.css
    types.ts
    vite-env.d.ts
```

工作区：

- `/videos`：登记视频路径或上传本地视频，查看处理状态，启动转写和候选切片任务。
- `/clips`：查看候选切片，确认、拒绝、异步生成视频切片、生成发布计划。
- `/publish`：导出 CSV/JSON。
- `/jobs`：查询任务状态、错误、trace_id，支持失败任务手动重新入队和删除。
- `/chains`：查看 LangChain 调用记录。

接口访问：

- 前端代码只请求 `/api/v1/video-ops/...` 相对地址。
- 请求层使用浏览器原生 `fetch`，不引入 axios。
- 文件上传使用 `FormData`，不手动设置 `Content-Type`，由浏览器生成 multipart boundary。
- Vite 开发服务通过 `server.proxy` 把 `/api` 转发到 `http://127.0.0.1:8000`。
- 前端不需要 `.env` 配置后端地址。

交互原则：

- 首屏直接进入视频运营工作台。
- 长任务通过任务 ID 查询状态。
- 所有失败状态展示错误原因。
- 人工审核是发布清单生成前的必经步骤。

## 10. 异步任务

任务类型：

- `transcribe_video`
- `detect_clips`
- `export_clip_video`

任务状态：

- `pending`
- `running`
- `succeeded`
- `failed`

失败策略：

- 错误摘要写入 `agent_tasks.error`。
- 结构化错误写入 `agent_tasks.error_json`，包含 `code`、`message`、`error_type`、`stage`、`details`、`retryable`、`recorded_at`。
- 前端 `任务监控` 工作区可查看错误摘要和结构化错误详情。
- `POST /jobs/{job_id}/retry` 只允许手动触发，把失败任务重新放入 Redis/RQ 队列。
- `DELETE /jobs/{job_id}` 只允许手动删除失败任务记录。
- 系统不做自动重新入队，避免失败任务循环调用大模型造成成本消耗。

RQ 队列名：

```text
video_ops
```

worker 启动入口：

```bash
cd backend
python scripts/run_worker.py
```

开发环境默认启动 1 个 worker，任务按顺序执行，便于控制本机 CPU、内存、ffmpeg 和大模型 API 调用压力。如果硬件资源和模型额度充足，可以在多个终端重复执行同一条 worker 命令，多个 worker 会共同消费 `video_ops` 队列。

当前任务执行链路：

```text
FastAPI 创建 agent_tasks 记录
-> enqueue_video_task()/enqueue_clip_export_task() 把任务放入 Redis/RQ 的 video_ops 队列
-> scripts/run_worker.py 启动 SimpleWorker
-> worker 执行 backend/app/jobs/pipeline.py
-> mark_task_running()/mark_task_succeeded()/mark_task_failed() 回写任务状态和结构化失败原因
```

视频切片导出链路：

```text
前端在已确认切片上点击“生成视频切片”
-> POST /api/v1/video-ops/clips/{clip_id}/export
-> 创建 export_clip_video 任务，切片 export_status=pending
-> RQ worker 执行 export_clip_video_job()
-> ExportClipVideoTool 调用 ffmpeg
-> 成功：video_clips.export_status=exported，clip_file_uri 写入输出 mp4 路径
-> 失败：video_clips.export_status=failed，export_error 和 agent_tasks.error_json 写入失败原因
```

## 11. 降级策略

ASR 不可用：

- `TranscriptionService(mock=True)` 返回 demo transcript。
- 仍能演示切片、文案和审核流程。

LLM 不可用：

- `.env` 设置 `LLM_MOCK=true`。
- LangChain chain 使用 mock structured output。
- `CandidateDetectionChain` 的 mock 模式会生成可演示候选片段，真实模型不可用时仍能跑通本地流程。

ffmpeg 不可用：

- 转写阶段如果依赖真实音频提取，会失败并写入任务错误。
- 已存在 transcript 的候选切片、审核、发布计划流程仍可演示。
- 视频切片导出任务会失败，失败原因写入 `agent_tasks.error_json` 和 `video_clips.export_error`，可在安装 ffmpeg 后手动重新导出。

切片质量差：

- 调整 `CandidateDetectionChain` 的提示词、输出约束和候选数量。
- 调整普通代码里的时间边界、最大时长和重叠去重阈值。
- 增加人工标注样本作为评测集。

## 12. 本地启动

准备数据库：

建库 SQL 文件：

```text
backend/scripts/create_database.sql
```

```sql
CREATE DATABASE "live-stream-clip-agent";
```

后端 API：

```powershell
cd C:\Users\36183\Desktop\working\demo3\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
``

后端启动必须使用本项目 `backend\.venv` 内的 Python，不使用系统全局 Python。

后端启动时会自动执行 `backend/app/db/init_sql.py` 中的建表 SQL。

RQ worker：

```powershell
cd C:\Users\36183\Desktop\working\demo3\backend
.\.venv\Scripts\python.exe scripts/run_worker.py
```

开发环境保持 1 个 worker 即可。如果要临时测试并发，可以再打开一个终端执行同一条命令。

如需在终端查看完整建表 SQL：

```powershell
cd C:\Users\36183\Desktop\working\demo3\backend
.\.venv\Scripts\python.exe scripts/init_db.py
```

前端：

```powershell
cd C:\Users\36183\Desktop\working\demo3\frontend
pnpm install
pnpm dev
```

Vite 会把前端请求的 `/api` 代理到本地后端 `http://127.0.0.1:8000`。

打开：

```text
http://127.0.0.1:5173
```

## 13. 测试与验收

后端核心单元测试：

```powershell
cd C:\Users\36183\Desktop\working\demo3\backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -t .
```

验收流程：

1. 新建数据库 `live-stream-clip-agent`。
2. 启动后端，由 `init_sql.py` 自动建表。
3. 前端登记 3 个视频。
4. 每个视频执行转写。
5. 每个视频执行候选切片生成。
6. 每个视频至少生成 5 个候选切片。
7. 人工确认切片。
8. 点击“生成视频切片”，等待导出任务完成。
9. 生成发布计划。
10. 导出 CSV 和 JSON。
11. 在 `Chain Runs` 工作区查看 LangChain 调用记录。

浏览器验收：

- 页面不空白。
- 核心按钮可见。
- 输入框、表格、标签、时间轴布局正常。
- 文案无乱码。
- 文本不溢出。
- CSV/JSON 导出入口可用。

## 14. 后续扩展

- 接入真实 Whisper-compatible ASR。
- 对接 MinIO。
- 自动截取封面帧。
- 把人工确认切片写入项目四 AI 素材中心的预留接口。
- 把调用记录接入 LangSmith。
