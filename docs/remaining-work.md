# 直播切片 Agent 未完成事项清单

这个文档只记录当前项目还没做完的内容。每完成一项并通过验证后，直接删除对应条目，不需要保留历史。

## 维护规则

- 只写还没完成的事情。
- 每条必须能被验证。
- 做完一条删掉一条。
- 如果实现过程中发现新问题，补到对应分组里。

## 后端必补

### 1. 真实 ASR 联调验收

当前状态：

- `backend/app/services/transcription.py` 已支持 `mock` 和 `aliyun_qwen3_asr_flash`。
- `aliyun_qwen3_asr_flash` 会将本地视频用 ffmpeg 抽成 mp3，再以 Base64 Data URL 调用 qwen3-asr-flash。
- qwen3-asr-flash 限制单段音频不超过 5 分钟，后续上传或转写前需要保证视频时长不超过 5 分钟。
- ffmpeg 已用于人工审核后的短视频切片导出。
- 还没有使用真实 DashScope API Key 和真实视频完成联调验收。

涉及文件：

- `backend/app/services/transcription.py`
- `backend/app/jobs/pipeline.py`
- `backend/app/core/config.py`
- `backend/.env.example`
- `docs/technical-design.md`

完成标准：

- 配置 `ASR_PROVIDER=aliyun_qwen3_asr_flash` 和真实 `ASR_API_KEY` 后，能调用 qwen3-asr-flash。
- 本地上传视频能先抽取音频，再完成转写。
- ASR 返回文本能写入 `transcript_segments`，时间段按视频总时长近似分配。
- mock 模式仍然保留，便于没有 ASR 环境时演示。

验证方式：

- 使用 5 分钟以内真实视频执行转写。
- `transcript_segments` 里出现真实转写文本和近似时间段。
- mock=true 时仍能跑通 demo 流程。

### 2. LangChain 模型配置化

当前状态：

- chain 代码里仍有硬编码模型名 `gpt-4.1-mini`。
- `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` 已在配置里定义，但 chain 还没有完整使用。

涉及文件：

- `backend/app/chains/candidate_detection.py`
- `backend/app/chains/clip_scoring.py`
- `backend/app/chains/publish_copy.py`
- `backend/app/chains/risk_review.py`
- `backend/app/core/config.py`
- `backend/tests/test_langchain_fallback.py`

完成标准：

- 所有 chain 从 `Settings` 读取模型配置。
- 没有 API key 或 `LLM_MOCK=true` 时使用 mock fallback。
- 真实模型调用失败时有清晰错误日志，并能按预期降级。
- 测试覆盖 mock、配置缺失、模型异常 fallback。

验证方式：

- `LLM_MOCK=true` 跑通本地流程。
- 配置真实 key 后，切片评分、文案生成、风险审核能调用真实模型。

### 3. 补 API 端到端集成测试

当前状态：

- 已有后端单元测试和分散的接口测试。
- 还缺从视频登记到发布清单导出的完整 API 流程测试。

涉及文件：

- `backend/tests/`
- `backend/app/api/v1/`
- `backend/app/services/`

完成标准：

- 新增一条不依赖真实 LLM 的完整 API 流程测试。
- 测试串联视频登记、转写任务创建、候选切片生成、人工审核、发布计划生成、CSV/JSON 导出。

验证方式：

- `python -m unittest discover -s tests -t .` 通过。
- 测试不依赖真实 LLM。

## 可选增强

### 4. MinIO 对象存储适配

当前状态：

- 项目文档预留 MinIO。
- 当前实际使用本地文件存储。

完成标准：

- 本地存储和 MinIO 可以通过配置切换。
- API 不暴露存储实现差异。
- 上传、读取、删除路径行为一致。

### 5. LangSmith 观测接入

当前状态：

- 配置里有 `LANGSMITH_TRACING`。
- 还没有完整接入 LangSmith trace。

完成标准：

- 开启配置后，LangChain 调用能进入 LangSmith。
- 关闭配置时不影响本地运行。
- `chain_runs.trace_id` 能和观测平台关联。

### 6. 自动封面帧

当前状态：

- 已有切片时间段和封面文案。
- 已支持人工审核后异步导出短视频文件。
- 还没有真正从视频里截取封面帧。

完成标准：

- 能根据 `start_sec` 截取封面帧。
- 封面帧路径写入数据库。
- 前端能查看封面帧路径或预览图。

### 7. 项目四素材中心预留接口

当前状态：

- 技术文档提到后续可把人工确认切片写入项目四 AI 素材中心。
- 当前还没有跨项目接口。

完成标准：

- 明确项目四接收的数据结构。
- 发布清单或已确认切片可以同步到项目四。
- 同步失败不影响当前项目的审核和导出流程。
