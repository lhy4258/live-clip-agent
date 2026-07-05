# 直播切片 Agent 未完成事项清单

这个文档只记录当前项目还没做完的内容。每完成一项并通过验证后，直接删除对应条目，不需要保留历史。

## 维护规则

- 只写还没完成的事情。
- 每条必须能被验证。
- 做完一条删掉一条。
- 如果实现过程中发现新问题，补到对应分组里。

## 后端必补

### 1. 接入真实 ASR 和 ffmpeg 音频处理

当前状态：

- `backend/app/services/transcription.py` 默认返回 mock 转写。
- `mock=False` 时会抛出 `NotImplementedError`。
- ffmpeg 依赖已规划，但真实音频提取和 ASR 调用还没接入。

涉及文件：

- `backend/app/services/transcription.py`
- `backend/app/jobs/pipeline.py`
- `backend/app/core/config.py`
- `backend/requirements.txt`
- `docs/technical-design.md`

完成标准：

- 支持从视频文件提取音频。
- 支持调用 Whisper-compatible ASR 或明确配置的本地/远程 ASR。
- ASR 返回内容能写入 `transcript_segments`。
- mock 模式仍然保留，便于没有 ASR 环境时演示。

验证方式：

- 使用真实视频执行转写。
- `transcript_segments` 里出现真实时间戳和文本。
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

- 已有后端单元测试。
- 还缺从视频登记到发布清单导出的完整 API 流程测试。

涉及文件：

- `backend/tests/`
- `backend/app/api/v1/`
- `backend/app/services/`

完成标准：

- 覆盖视频登记。
- 覆盖转写任务创建。
- 覆盖候选切片生成。
- 覆盖人工审核。
- 覆盖发布计划生成。
- 覆盖 CSV/JSON 导出。

验证方式：

- `python -m unittest discover -s tests -t .` 通过。
- 测试不依赖真实 LLM。

## 前端必补

### 4. 任务监控页补自动刷新

当前状态：

- 前端已有任务监控页面。
- 长任务状态查看仍偏手动。

涉及文件：

- `frontend/src/views/JobMonitorView.vue`
- `frontend/src/composables/useVideoOps.ts`

完成标准：

- 对 `pending` 和 `running` 任务自动轮询。
- 任务完成或失败后停止轮询。
- 页面离开时停止定时器。
- 失败原因能完整展示。

验证方式：

- 发起转写任务。
- 不手动刷新页面，状态可以自动更新。

## 可选增强

### 5. MinIO 对象存储适配

当前状态：

- 项目文档预留 MinIO。
- 当前实际使用本地文件存储。

完成标准：

- 本地存储和 MinIO 可以通过配置切换。
- API 不暴露存储实现差异。
- 上传、读取、删除路径行为一致。

### 6. LangSmith 观测接入

当前状态：

- 配置里有 `LANGSMITH_TRACING`。
- 还没有完整接入 LangSmith trace。

完成标准：

- 开启配置后，LangChain 调用能进入 LangSmith。
- 关闭配置时不影响本地运行。
- `chain_runs.trace_id` 能和观测平台关联。

### 7. 自动封面帧和简单裁剪导出

当前状态：

- 已有切片时间段和封面文案。
- 还没有真正从视频里截封面或导出短视频文件。

完成标准：

- 能根据 `start_sec` 截取封面帧。
- 能按 `start_sec` 和 `end_sec` 导出短视频文件。
- 导出结果可被前端下载或查看。

### 8. 项目四素材中心预留接口

当前状态：

- 技术文档提到后续可把人工确认切片写入项目四 AI 素材中心。
- 当前还没有跨项目接口。

完成标准：

- 明确项目四接收的数据结构。
- 发布清单或已确认切片可以同步到项目四。
- 同步失败不影响当前项目的审核和导出流程。
