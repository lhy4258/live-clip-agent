<script setup lang="ts">
import { useVideoOpsContext } from '../composables/videoOpsContext'
import { formatDateTime, platformText } from '../utils/format'

const { publishPlans, loadPublishPlans, download } = useVideoOpsContext()

function handleExport(command: string | number | object) {
  if (command === 'csv' || command === 'json') download(command)
}
</script>

<template>
  <section class="page-section">
    <div class="page-toolbar">
      <div>
        <div class="page-label">发布清单</div>
        <h2>导出人工确认后的运营素材</h2>
      </div>
      <div class="toolbar-actions">
        <el-button @click="loadPublishPlans">刷新</el-button>
      </div>
    </div>

    <div class="plain-table-section">
      <div class="plain-table-toolbar">
        <strong>发布计划</strong>
        <el-dropdown trigger="click" @command="handleExport">
          <el-button type="primary">导出</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="csv">导出 CSV</el-dropdown-item>
              <el-dropdown-item command="json">导出 JSON</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      <el-table
        v-if="publishPlans.length"
        :data="publishPlans"
        row-key="id"
        height="calc(100vh - 240px)"
        class="publish-table wrap-table direct-table"
      >
        <el-table-column label="创建时间" width="140" align="center" header-align="center">
          <template #default="{ row }">{{ formatDateTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="平台" width="76" align="center" header-align="center">
          <template #default="{ row }">{{ platformText(row.platform) }}</template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="150" align="center" header-align="center" />
        <el-table-column prop="description" label="简介" min-width="220" align="center" header-align="center" />
        <el-table-column label="标签" width="150" align="center" header-align="center">
          <template #default="{ row }">
            <div class="tag-row compact-tags">
              <el-tag v-for="tag in row.hashtags" :key="`${row.id}-${tag}`" effect="plain">
                {{ tag }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else class="plain-empty" description="暂无发布计划，请先在切片审核区生成。" />
    </div>
  </section>
</template>
