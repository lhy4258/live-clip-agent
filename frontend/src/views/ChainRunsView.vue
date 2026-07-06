<script setup lang="ts">
import { useVideoOpsContext } from '../composables/videoOpsContext'

const { traceId, chainRuns, loadChains } = useVideoOpsContext()
</script>

<template>
  <section class="page-section">
    <div class="page-toolbar">
      <div>
        <div class="page-label">Chain Runs</div>
        <h2>LangChain 调用记录</h2>
      </div>
      <div class="toolbar-actions">
        <el-input
          v-model="traceId"
          class="inline-input"
          placeholder="trace_id 可选"
        />
        <el-button type="primary" @click="loadChains">查询</el-button>
      </div>
    </div>

    <el-card shadow="never" class="work-card">
      <el-table :data="chainRuns" row-key="id" height="520" class="wrap-table">
        <el-table-column prop="chain_name" label="Chain" width="130" />
        <el-table-column prop="prompt_version" label="Prompt" width="130" />
        <el-table-column prop="model" label="模型" width="120" />
        <el-table-column prop="latency_ms" label="耗时" width="80" />
        <el-table-column prop="trace_id" label="Trace" min-width="180" />
        <el-table-column prop="error" label="错误" min-width="160" />
      </el-table>
    </el-card>
  </section>
</template>
