<script setup lang="ts">
import { useVideoOpsContext } from '../composables/videoOpsContext'
import { tagType } from '../utils/format'

const { busy, clips, selectedClip, clipStatus, loadClips, openClip, submitReview, submitPublishPlan } =
  useVideoOpsContext()
</script>

<template>
  <section class="page-section">
    <div class="page-toolbar">
      <div>
        <div class="page-label">切片审核</div>
        <h2>候选切片审核与发布准备</h2>
      </div>
      <div class="toolbar-actions">
        <el-select v-model="clipStatus" class="status-select">
          <el-option label="全部" value="" />
          <el-option label="候选" value="candidate" />
          <el-option label="已确认" value="approved" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
        <el-button @click="loadClips">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="14">
        <el-card shadow="never" class="work-card">
          <template #header>
            <span>候选切片</span>
          </template>
          <el-table :data="clips" row-key="id" height="520" @row-click="openClip">
            <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
            <el-table-column label="评分" width="90">
              <template #default="{ row }">{{ Math.round(row.score * 100) }}</template>
            </el-table-column>
            <el-table-column prop="risk_level" label="风险" width="100">
              <template #default="{ row }">
                <el-tag :type="tagType(row.risk_level)" effect="light">{{ row.risk_level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="tagType(row.status)" effect="light">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card shadow="never" class="work-card">
          <template #header>
            <span>{{ selectedClip?.title || '切片详情' }}</span>
          </template>
          <template v-if="selectedClip">
            <p class="detail-summary">{{ selectedClip.summary }}</p>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="时间">{{ selectedClip.start_sec }}s - {{ selectedClip.end_sec }}s</el-descriptions-item>
              <el-descriptions-item label="评分">{{ Math.round(selectedClip.score * 100) }}</el-descriptions-item>
              <el-descriptions-item label="状态">{{ selectedClip.status }}</el-descriptions-item>
              <el-descriptions-item label="风险">{{ selectedClip.risk_level }}</el-descriptions-item>
            </el-descriptions>
            <div class="cover-copy">封面文案：{{ selectedClip.cover_text }}</div>
            <div class="tag-row">
              <el-tag v-for="tag in selectedClip.tags" :key="tag" effect="plain">{{ tag }}</el-tag>
            </div>
            <div class="toolbar-actions">
              <el-button type="primary" :disabled="busy" @click="submitReview('approved')">确认</el-button>
              <el-button type="danger" :disabled="busy" @click="submitReview('rejected')">拒绝</el-button>
              <el-button :disabled="busy" @click="submitPublishPlan">生成发布计划</el-button>
            </div>
          </template>
          <el-empty v-else description="暂无切片数据" />
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>
