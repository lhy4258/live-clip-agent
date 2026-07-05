<script setup lang="ts">
import { useVideoOpsContext } from '../composables/videoOpsContext'

const { download } = useVideoOpsContext()
</script>

<template>
  <section class="page-section">
    <div class="page-toolbar">
      <div>
        <div class="page-label">发布清单</div>
        <h2>导出人工确认后的运营素材</h2>
      </div>
      <div class="toolbar-actions">
        <el-button type="primary" @click="download('csv')">导出 CSV</el-button>
        <el-button @click="download('json')">导出 JSON</el-button>
      </div>
    </div>

    <el-card shadow="never" class="work-card">
      <el-empty description="发布计划由切片审核区生成，导出接口会返回当前发布清单。" />
    </el-card>
  </section>
</template>
