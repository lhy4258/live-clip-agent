<script setup lang="ts">
import { ref } from 'vue'
import { useVideoOpsContext } from '../composables/videoOpsContext'
import { formatTime, tagType } from '../utils/format'

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
        <el-button type="primary" :disabled="!selectedVideo || busy" @click="runTranscribe">转写</el-button>
        <el-button type="primary" :disabled="!selectedVideo || busy" @click="runDetect">生成候选切片</el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <el-col :xs="24" :lg="10">
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
              <el-input v-model="videoForm.source" />
            </el-form-item>
            <el-form-item label="授权">
              <el-input v-model="videoForm.license" />
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

      <el-col :xs="24" :lg="14">
        <el-card shadow="never" class="work-card">
          <template #header>
            <span>视频列表</span>
          </template>
          <el-table :data="videos" row-key="id" height="356" @row-click="openVideo">
            <el-table-column prop="title" label="标题" min-width="180" />
            <el-table-column prop="source" label="来源" width="120" />
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="tagType(row.status)" effect="light">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <el-row v-if="selectedVideo" :gutter="16">
      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="work-card">
          <template #header>
            <span>{{ selectedVideo.title }}</span>
          </template>
          <p class="muted compact-text">{{ selectedVideo.file_uri }}</p>
          <video ref="playerRef" class="video-player" controls :src="selectedVideo.file_uri"></video>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="来源">{{ selectedVideo.source }}</el-descriptions-item>
            <el-descriptions-item label="授权">{{ selectedVideo.license }}</el-descriptions-item>
            <el-descriptions-item label="时长">{{ selectedVideo.duration_sec ?? '-' }}s</el-descriptions-item>
            <el-descriptions-item label="状态">{{ selectedVideo.status }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card shadow="never" class="work-card">
          <template #header>
            <span>转写时间轴</span>
          </template>
          <el-scrollbar height="330px">
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
