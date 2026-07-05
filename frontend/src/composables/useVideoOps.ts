import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createPublishPlan,
  createVideo,
  deleteJob,
  exportPublishPlansUrl,
  getClip,
  getJob,
  getVideo,
  listChainRuns,
  listClips,
  listTranscripts,
  listVideos,
  reviewClip,
  retryJob,
  startDetectClips,
  startTranscribe,
  uploadVideo,
} from '../api'
import type { AgentJob, ChainRun, SourceVideo, TranscriptSegment, VideoClip } from '../types'

export type TabKey = 'videos' | 'clips' | 'publish' | 'jobs' | 'chains'

export function useVideoOps() {
  const activeTab = ref<TabKey>('videos')
  const apiKey = ref(localStorage.getItem('video_ops_api_key') || 'dev-live-stream-clip-agent')
  const busy = ref(false)
  const statusMessage = ref('准备就绪')

  const videos = ref<SourceVideo[]>([])
  const selectedVideo = ref<SourceVideo | null>(null)
  const transcripts = ref<TranscriptSegment[]>([])
  const clips = ref<VideoClip[]>([])
  const selectedClip = ref<VideoClip | null>(null)
  const clipStatus = ref('')
  const jobId = ref('')
  const job = ref<AgentJob | null>(null)
  const traceId = ref('')
  const chainRuns = ref<ChainRun[]>([])
  const videoRef = ref<HTMLVideoElement | null>(null)
  const uploadFile = ref<File | null>(null)
  const uploadFileInputKey = ref(0)

  const videoForm = reactive({
    title: '',
    file_uri: '',
    source: 'self_recorded',
    license: 'self_owned',
    duration_sec: null as number | null,
  })

  const canCreateVideo = computed(() =>
    Boolean(videoForm.title && videoForm.file_uri && videoForm.source && videoForm.license),
  )

  function saveApiKey() {
    localStorage.setItem('video_ops_api_key', apiKey.value)
    statusMessage.value = 'API Key 已保存'
  }

  async function run(task: () => Promise<void>, message = '操作完成') {
    busy.value = true
    statusMessage.value = '处理中...'
    try {
      await task()
      statusMessage.value = message
    } catch (error) {
      const text = error instanceof Error ? error.message : '操作失败'
      statusMessage.value = text
      ElMessage.error(text)
    } finally {
      busy.value = false
    }
  }

  async function loadVideos() {
    videos.value = await listVideos()
    if (!selectedVideo.value && videos.value.length) await openVideo(videos.value[0])
  }

  async function submitVideo() {
    if (!canCreateVideo.value) return
    await run(async () => {
      if (uploadFile.value) {
        await uploadVideo({
          title: videoForm.title,
          source: videoForm.source,
          license: videoForm.license,
          duration_sec: videoForm.duration_sec,
          file: uploadFile.value,
        })
      } else {
        await createVideo({ ...videoForm })
      }
      videoForm.title = ''
      videoForm.file_uri = ''
      videoForm.duration_sec = null
      uploadFile.value = null
      uploadFileInputKey.value += 1
      await loadVideos()
    }, '视频已登记')
  }

  function selectUploadFile(event: Event) {
    const input = event.target as HTMLInputElement
    uploadFile.value = input.files?.[0] ?? null
    if (uploadFile.value) videoForm.file_uri = uploadFile.value.name
  }

  async function openVideo(video: SourceVideo) {
    selectedVideo.value = await getVideo(video.id)
    transcripts.value = await listTranscripts(video.id)
  }

  async function runTranscribe() {
    if (!selectedVideo.value) return
    await run(async () => {
      const created = await startTranscribe(selectedVideo.value!.id)
      jobId.value = created.id
      job.value = created
    }, '转写任务已创建')
  }

  async function runDetect() {
    if (!selectedVideo.value) return
    await run(async () => {
      const created = await startDetectClips(selectedVideo.value!.id)
      jobId.value = created.id
      job.value = created
    }, '切片任务已创建')
  }

  function seek(seconds: number) {
    if (!videoRef.value) return
    videoRef.value.currentTime = seconds
    void videoRef.value.play()
  }

  async function loadClips() {
    clips.value = await listClips(clipStatus.value || undefined)
    if (!selectedClip.value && clips.value.length) selectedClip.value = clips.value[0]
  }

  async function openClip(row: VideoClip) {
    selectedClip.value = await getClip(row.id)
  }

  async function submitReview(label: 'approved' | 'rejected') {
    if (!selectedClip.value) return
    const result = await ElMessageBox.prompt('请输入审核原因', '人工审核', {
      inputValue: label === 'approved' ? '内容可用' : '不适合发布',
    })
    await run(async () => {
      selectedClip.value = await reviewClip(selectedClip.value!.id, {
        label,
        reason: result.value,
        reviewer: 'operator',
      })
      await loadClips()
    }, '审核已保存')
  }

  async function submitPublishPlan() {
    if (!selectedClip.value) return
    await run(async () => {
      await createPublishPlan(selectedClip.value!.id, 'douyin')
    }, '发布计划已生成')
  }

  function download(format: 'csv' | 'json') {
    window.open(exportPublishPlansUrl(format), '_blank')
  }

  async function queryJob() {
    if (!jobId.value) return
    await run(async () => {
      job.value = await getJob(jobId.value)
    }, '任务已查询')
  }

  async function retryCurrentJob() {
    if (!job.value) return
    await run(async () => {
      job.value = await retryJob(job.value!.id)
    }, '任务已重新入队')
  }

  async function deleteCurrentJob() {
    if (!job.value) return
    try {
      await ElMessageBox.confirm('删除后只移除失败任务记录，不会删除视频、转写或切片数据。', '删除失败任务', {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      })
    } catch {
      return
    }
    await run(async () => {
      await deleteJob(job.value!.id)
      job.value = null
    }, '失败任务已删除')
  }

  async function loadChains() {
    chainRuns.value = await listChainRuns(traceId.value || undefined)
  }

  async function changeTab(tab: TabKey) {
    activeTab.value = tab
    if (tab === 'videos') await run(loadVideos, '视频列表已刷新')
    if (tab === 'clips') await run(loadClips, '切片列表已刷新')
    if (tab === 'chains') await run(loadChains, 'Chain Runs 已刷新')
  }

  onMounted(async () => {
    await loadVideos()
    await loadClips()
  })

  return {
    activeTab,
    apiKey,
    busy,
    statusMessage,
    videos,
    selectedVideo,
    transcripts,
    clips,
    selectedClip,
    clipStatus,
    jobId,
    job,
    traceId,
    chainRuns,
    videoRef,
    videoForm,
    canCreateVideo,
    uploadFileInputKey,
    saveApiKey,
    loadVideos,
    submitVideo,
    selectUploadFile,
    openVideo,
    runTranscribe,
    runDetect,
    seek,
    loadClips,
    openClip,
    submitReview,
    submitPublishPlan,
    download,
    queryJob,
    retryCurrentJob,
    deleteCurrentJob,
    loadChains,
    changeTab,
  }
}
