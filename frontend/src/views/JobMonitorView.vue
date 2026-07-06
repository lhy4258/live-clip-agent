<script setup lang="ts">
import { computed, onBeforeUnmount, watch } from 'vue'
import { useVideoOpsContext } from '../composables/videoOpsContext'
import type { AgentJob } from '../types'
import { statusText, tagType } from '../utils/format'

const { jobId, job, refreshJob, queryJob, retryCurrentJob, deleteCurrentJob } = useVideoOpsContext()

const activeJobStatuses = new Set(['pending', 'running'])
const isAutoRefreshing = computed(() => Boolean(job.value && activeJobStatuses.has(job.value.status)))
let refreshTimer: number | undefined
let refreshInFlight = false

function stopAutoRefresh() {
  if (refreshTimer === undefined) return
  window.clearInterval(refreshTimer)
  refreshTimer = undefined
}

function startAutoRefresh() {
  if (refreshTimer !== undefined) return
  refreshTimer = window.setInterval(async () => {
    if (!jobId.value || !job.value || !activeJobStatuses.has(job.value.status) || refreshInFlight) {
      stopAutoRefresh()
      return
    }
    refreshInFlight = true
    try {
      await refreshJob()
    } catch {
      stopAutoRefresh()
    } finally {
      refreshInFlight = false
    }
  }, 3000)
}

watch(
  isAutoRefreshing,
  (active) => {
    if (active) {
      startAutoRefresh()
    } else {
      stopAutoRefresh()
    }
  },
  { immediate: true },
)

onBeforeUnmount(stopAutoRefresh)

function errorText(row: AgentJob) {
  const message = row.error_json?.message
  return typeof message === 'string' && message ? message : row.error || '-'
}

function errorMeta(row: AgentJob, key: string) {
  const value = row.error_json?.[key]
  return typeof value === 'string' && value ? value : '-'
}

function hasErrorJson(row: AgentJob) {
  return Boolean(row.error_json && Object.keys(row.error_json).length)
}

function formatErrorJson(row: AgentJob) {
  return JSON.stringify(row.error_json, null, 2)
}
</script>

<template>
  <section class="page-section">
    <div class="page-toolbar">
      <div>
        <div class="page-label">任务监控</div>
        <h2>异步任务状态与错误追踪</h2>
      </div>
      <div class="toolbar-actions">
        <el-input
          v-model="jobId"
          class="inline-input"
          placeholder="job_id"
        />
        <el-button type="primary" @click="queryJob">查询</el-button>
        <el-button :disabled="!job || job.status !== 'failed'" @click="retryCurrentJob">重新入队</el-button>
        <el-button type="danger" plain :disabled="!job || job.status !== 'failed'" @click="deleteCurrentJob">
          删除失败任务
        </el-button>
      </div>
    </div>

    <el-card shadow="never" class="work-card">
      <template v-if="job">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="任务">{{ job.id }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ job.task_type }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="tagType(job.status)" effect="light">{{ statusText(job.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="Trace">{{ job.trace_id }}</el-descriptions-item>
          <el-descriptions-item label="失败原因" :span="2">{{ errorText(job) }}</el-descriptions-item>
          <el-descriptions-item label="错误类型">{{ errorMeta(job, 'error_type') }}</el-descriptions-item>
          <el-descriptions-item label="失败阶段">{{ errorMeta(job, 'stage') }}</el-descriptions-item>
          <el-descriptions-item label="结构化错误" :span="2">
            <pre v-if="hasErrorJson(job)" class="json-block">{{ formatErrorJson(job) }}</pre>
            <span v-else>-</span>
          </el-descriptions-item>
        </el-descriptions>
      </template>
      <el-empty v-else description="暂无任务数据" />
    </el-card>
  </section>
</template>
