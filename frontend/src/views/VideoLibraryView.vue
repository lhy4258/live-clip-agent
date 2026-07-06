<script setup lang="ts">
import { ref } from 'vue'
import { useVideoOpsContext } from '../composables/videoOpsContext'
import { formatTime, licenseText, sourceText, statusText, tagType } from '../utils/format'

const playerRef = ref<HTMLVideoElement | null>(null)
const {
  busy,
  videos,
  selectedVideo,
  transcripts,
  videoForm,
  canCreateVideo,
  uploadFileInputKey,
  loadVideos,
  submitVideo,
  selectUploadFile,
  openVideo,
  runTranscribe,
  runDetect,
  deleteVideoRow,
} = useVideoOpsContext()

function seek(seconds: number) {
  if (!playerRef.value) return
  playerRef.value.currentTime = seconds
  void playerRef.value.play()
}
</script>

<template>
  <section class="page-section">
    <div class="page-toolbar">
      <div>
        <div class="page-label">视频库</div>
        <h2>视频登记与 Agent 处理</h2>
      </div>
      <div class="toolbar-actions">
        <el-button @click="loadVideos">刷新</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="8">
        <el-card shadow="never" class="work-card">
          <template #header>
            <span>登记视频</span>
          </template>
          <el-form label-position="top" :model="videoForm">
            <el-form-item label="标题">
              <el-input v-model="videoForm.title" placeholder="例如：7月直播复盘" />
            </el-form-item>
            <el-form-item label="文件路径">
              <div class="path-picker-row">
                <el-input v-model="videoForm.file_uri" placeholder="C:/videos/live-demo.mp4 或 data/files/demo.mp4" />
                <input
                  id="video-upload-input"
                  :key="uploadFileInputKey"
                  class="file-input-hidden"
                  type="file"
                  accept="video/*"
                  @change="selectUploadFile"
                />
                <label class="file-picker" for="video-upload-input">选择视频</label>
              </div>
            </el-form-item>
            <el-form-item label="来源">
              <el-select v-model="videoForm.source">
                <el-option label="自录直播" value="self_recorded" />
                <el-option label="课程回放" value="course_replay" />
              </el-select>
            </el-form-item>
            <el-form-item label="授权">
              <el-select v-model="videoForm.license">
                <el-option label="自有授权" value="self_owned" />
                <el-option label="已授权" value="authorized" />
              </el-select>
            </el-form-item>
            <el-form-item label="时长（秒，可选）">
              <el-input-number v-model="videoForm.duration_sec" :min="0" :step="10" controls-position="right" />
            </el-form-item>
            <div class="form-actions">
              <el-button type="primary" :disabled="!canCreateVideo || busy" @click="submitVideo">登记视频</el-button>
            </div>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="16">
        <el-card shadow="never" class="work-card">
          <template #header>
            <span>视频列表</span>
          </template>
          <el-table :data="videos" row-key="id" height="432" class="wrap-table video-list-table" @row-click="openVideo">
            <el-table-column prop="title" label="标题" min-width="132" />
            <el-table-column label="来源" width="96" align="center" header-align="center">
              <template #default="{ row }">{{ sourceText(row.source) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="86" align="center" header-align="center">
              <template #default="{ row }">
                <el-tag :type="tagType(row.status)" effect="light">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="264" align="center" header-align="center">
              <template #default="{ row }">
                <div class="table-actions">
                  <el-button type="primary" size="small" :disabled="busy" @click.stop="runTranscribe(row)">转写</el-button>
                  <el-button type="primary" size="small" :disabled="busy" @click.stop="runDetect(row)">
                    生成候选切片
                  </el-button>
                  <el-button type="danger" size="small" :disabled="busy" @click.stop="deleteVideoRow(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row v-if="selectedVideo" :gutter="16" class="equal-height-row media-detail-row">
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="work-card media-card">
          <template #header>
            <span>{{ selectedVideo.title }}</span>
          </template>
          <p class="muted compact-text">{{ selectedVideo.file_uri }}</p>
          <video ref="playerRef" class="video-player" controls :src="selectedVideo.file_uri"></video>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="来源">{{ sourceText(selectedVideo.source) }}</el-descriptions-item>
            <el-descriptions-item label="授权">{{ licenseText(selectedVideo.license) }}</el-descriptions-item>
            <el-descriptions-item label="时长">{{ selectedVideo.duration_sec ?? '-' }}s</el-descriptions-item>
            <el-descriptions-item label="状态">{{ statusText(selectedVideo.status) }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="work-card timeline-card">
          <template #header>
            <span>转写时间轴</span>
          </template>
          <el-scrollbar class="timeline-scroll" height="100%">
            <button
              v-for="segment in transcripts"
              :key="segment.id"
              class="timeline-row"
              type="button"
              @click="seek(segment.start_sec)"
            >
              <strong>{{ formatTime(segment.start_sec) }} - {{ formatTime(segment.end_sec) }}</strong>
              <span>{{ segment.text }}</span>
            </button>
            <el-empty v-if="!transcripts.length" description="暂无转写片段" />
          </el-scrollbar>
        </el-card>
      </el-col>
    </el-row>
  </section>
</template>
