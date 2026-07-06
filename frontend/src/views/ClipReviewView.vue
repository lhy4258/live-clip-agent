<script setup lang="ts">
import { useVideoOpsContext } from '../composables/videoOpsContext'
import { exportStatusText, riskText, statusText, tagType } from '../utils/format'
import type { VideoClip } from '../types'

const {
  busy,
  clips,
  selectedClip,
  coverTextDraft,
  clipStatus,
  loadClips,
  openClip,
  deleteClipRow,
  submitReview,
  submitPublishPlan,
  saveCoverText,
  submitExportClip,
} = useVideoOpsContext()

function canExportClip(clip: VideoClip) {
  return clip.status === 'approved' && ['not_started', 'failed'].includes(clip.export_status)
}

function canDeleteClip(clip: VideoClip) {
  return clip.status !== 'approved'
}

function exportButtonText(clip: VideoClip) {
  if (clip.export_status === 'failed') return '重新生成视频切片'
  if (['pending', 'exporting'].includes(clip.export_status)) return '导出中'
  if (clip.export_status === 'exported') return '已生成视频切片'
  return '生成视频切片'
}
</script>

<template>
  <section class="page-section">
    <div class="page-toolbar">
      <div>
        <div class="page-label">切片审核</div>
        <h2>候选切片审核与发布准备</h2>
      </div>
      <div class="toolbar-actions">
        <el-select v-model="clipStatus" class="status-select" placeholder="全部">
          <el-option label="全部" value="" />
          <el-option label="待确认" value="candidate" />
          <el-option label="已确认" value="approved" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
        <el-button @click="loadClips">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16" class="review-workspace-row">
      <el-col :xs="24" :lg="16">
        <el-card shadow="never" class="work-card review-workspace-card">
          <template #header>
            <span>候选切片</span>
          </template>
          <el-table
            :data="clips"
            row-key="id"
            height="calc(100vh - 284px)"
            class="wrap-table"
            @row-click="openClip"
          >
            <el-table-column prop="title" label="标题" min-width="100" header-align="center" />
            <el-table-column
              prop="source_video_title"
              label="来源视频"
              width="128"
              align="center"
              header-align="center"
            />
            <el-table-column label="评分" width="54" align="center" header-align="center">
              <template #default="{ row }">{{ Math.round(row.score * 100) }}</template>
            </el-table-column>
            <el-table-column label="风险" width="58" align="center" header-align="center">
              <template #default="{ row }">
                <el-tag :type="tagType(row.risk_level)" effect="light">{{ riskText(row.risk_level) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="74" align="center" header-align="center">
              <template #default="{ row }">
                <el-tag :type="tagType(row.status)" effect="light">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="参考" width="76" align="center" header-align="center">
              <template #default="{ row }">
                <el-tag v-if="row.is_editable" type="warning" effect="light">可修改</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="导出" width="72" align="center" header-align="center">
              <template #default="{ row }">
                <el-tag :type="tagType(row.export_status)" effect="light">
                  {{ exportStatusText(row.export_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="72" align="center" header-align="center">
              <template #default="{ row }">
                <el-button
                  v-if="canDeleteClip(row)"
                  type="danger"
                  size="small"
                  :disabled="busy"
                  @click.stop="deleteClipRow(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="8">
        <el-card shadow="never" class="work-card review-workspace-card">
          <template #header>
            <span>{{ selectedClip?.title || '切片详情' }}</span>
          </template>
          <template v-if="selectedClip">
            <p class="detail-summary">{{ selectedClip.summary }}</p>
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="来源视频">{{ selectedClip.source_video_title }}</el-descriptions-item>
              <el-descriptions-item label="时间">{{ selectedClip.start_sec }}s - {{ selectedClip.end_sec }}s</el-descriptions-item>
              <el-descriptions-item label="评分">{{ Math.round(selectedClip.score * 100) }}</el-descriptions-item>
              <el-descriptions-item label="状态">{{ statusText(selectedClip.status) }}</el-descriptions-item>
              <el-descriptions-item label="参考">
                <el-tag v-if="selectedClip.is_editable" type="warning" effect="light">可修改</el-tag>
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item label="风险">{{ riskText(selectedClip.risk_level) }}</el-descriptions-item>
              <el-descriptions-item label="导出">{{ exportStatusText(selectedClip.export_status) }}</el-descriptions-item>
              <el-descriptions-item v-if="selectedClip.is_editable" label="修改建议">
                {{ selectedClip.edit_suggestion || '-' }}
              </el-descriptions-item>
              <el-descriptions-item v-if="selectedClip.is_editable" label="修改原因">
                {{ selectedClip.edit_reason || '-' }}
              </el-descriptions-item>
              <el-descriptions-item v-if="selectedClip.clip_file_uri" label="切片文件">
                {{ selectedClip.clip_file_uri }}
              </el-descriptions-item>
              <el-descriptions-item v-if="selectedClip.export_error" label="失败原因">
                {{ selectedClip.export_error }}
              </el-descriptions-item>
            </el-descriptions>
            <div class="cover-editor">
              <div class="field-caption">封面文案</div>
              <div class="cover-edit-row">
                <el-input v-model="coverTextDraft" maxlength="120" show-word-limit />
                <el-button :disabled="busy || coverTextDraft === selectedClip.cover_text" @click="saveCoverText">
                  保存
                </el-button>
              </div>
            </div>
            <div class="tag-row">
              <span class="tag-label">内容标签</span>
              <el-tag v-for="tag in selectedClip.tags" :key="`${selectedClip.id}-${tag}`" effect="plain">
                {{ tag }}
              </el-tag>
            </div>
            <div class="toolbar-actions">
              <el-button type="primary" :disabled="busy" @click="submitReview('approved')">确认</el-button>
              <el-button type="danger" :disabled="busy" @click="submitReview('rejected')">拒绝</el-button>
              <el-button
                v-if="selectedClip.status === 'approved'"
                type="success"
                :disabled="busy || !canExportClip(selectedClip)"
                @click="submitExportClip"
              >
                {{ exportButtonText(selectedClip) }}
              </el-button>
              <el-button v-if="selectedClip.status === 'approved'" :disabled="busy" @click="submitPublishPlan">
                生成发布计划
              </el-button>
            </div>
          </template>
          <el-empty v-else description="暂无切片数据" />
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>
