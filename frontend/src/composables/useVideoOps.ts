import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createPublishPlan,
  createVideo,
  deleteClip,
  deleteVideo,
  deleteJob,
  exportClip,
  exportPublishPlansUrl,
  getClip,
  getJob,
  getVideo,
  listChainRuns,
  listClips,
  listPublishPlans,
  listTranscripts,
  listVideos,
  reviewClip,
  retryJob,
  startDetectClips,
  startTranscribe,
  updateClipCoverText,
  uploadVideo,
} from '../api'
import type { AgentJob, ChainRun, PublishPlan, SourceVideo, TranscriptSegment, VideoClip } from '../types'

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
  const coverTextDraft = ref('')
  const publishPlans = ref<PublishPlan[]>([])
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

  function setSelectedClip(clip: VideoClip | null) {
    selectedClip.value = clip
    coverTextDraft.value = clip?.cover_text || ''
  }

  async function run(task: () => Promise<void>, message = '操作完成', notify = false) {
    busy.value = true
    statusMessage.value = '处理中...'
    try {
      await task()
      statusMessage.value = message
      if (notify) ElMessage.success(message)
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

  async function runTranscribe(video: SourceVideo | null = selectedVideo.value) {
    if (!video) return
    await run(async () => {
      const created = await startTranscribe(video.id)
      jobId.value = created.id
      job.value = created
      await loadVideos()
    }, `“${video.title}”转写任务已创建`)
  }

  async function runDetect(video: SourceVideo | null = selectedVideo.value) {
    if (!video) return
    await run(async () => {
      const created = await startDetectClips(video.id)
      jobId.value = created.id
      job.value = created
      await loadVideos()
    }, `“${video.title}”候选切片任务已创建`)
  }

  async function deleteVideoRow(video: SourceVideo) {
    try {
      await ElMessageBox.confirm(
        `确认删除视频“${video.title}”吗？删除后会同步移除它的转写、候选切片和发布计划。`,
        '删除登记视频',
        {
          type: 'warning',
          confirmButtonText: '删除',
          cancelButtonText: '取消',
        },
      )
    } catch {
      return
    }
    await run(async () => {
      await deleteVideo(video.id)
      if (selectedVideo.value?.id === video.id) {
        selectedVideo.value = null
        transcripts.value = []
      }
      await loadVideos()
      await loadClips()
      await loadPublishPlans()
    }, '视频已删除', true)
  }

  function seek(seconds: number) {
    if (!videoRef.value) return
    videoRef.value.currentTime = seconds
    void videoRef.value.play()
  }

  async function loadClips() {
    const currentId = selectedClip.value?.id
    clips.value = await listClips(clipStatus.value || undefined)
    if (currentId) {
      setSelectedClip(clips.value.find((clip) => clip.id === currentId) || clips.value[0] || null)
    } else if (clips.value.length) {
      setSelectedClip(clips.value[0])
    }
  }

  async function openClip(row: VideoClip) {
    setSelectedClip(await getClip(row.id))
  }

  async function deleteClipRow(clip: VideoClip) {
    try {
      await ElMessageBox.confirm(`确认删除切片“${clip.title}”吗？删除后不会再进入发布清单。`, '删除切片', {
        type: 'warning',
        confirmButtonText: '删除',
        cancelButtonText: '取消',
      })
    } catch {
      return
    }
    await run(async () => {
      await deleteClip(clip.id)
      await loadClips()
      await loadPublishPlans()
    }, '切片已删除', true)
  }

  async function submitReview(label: 'approved' | 'rejected') {
    if (!selectedClip.value) return
    const result = await ElMessageBox.prompt('请输入审核原因', '人工审核', {
      inputValue: label === 'approved' ? '内容可用' : '不适合发布',
    })
    await run(async () => {
      setSelectedClip(await reviewClip(selectedClip.value!.id, {
        label,
        reason: result.value,
        reviewer: 'operator',
      }))
      await loadClips()
    }, '审核已保存', true)
  }

  async function submitPublishPlan() {
    if (!selectedClip.value) return
    if (selectedClip.value.status !== 'approved') {
      ElMessage.warning('请先确认切片，再生成发布计划')
      return
    }
    await run(async () => {
      await createPublishPlan(selectedClip.value!.id, 'douyin')
      await loadPublishPlans()
    }, '发布计划已生成，可到发布清单查看', true)
  }

  async function saveCoverText() {
    if (!selectedClip.value) return
    const clipId = selectedClip.value.id
    await run(async () => {
      setSelectedClip(await updateClipCoverText(clipId, coverTextDraft.value.trim()))
      await loadClips()
    }, '封面文案已保存', true)
  }

  async function submitExportClip() {
    if (!selectedClip.value) return
    const clipId = selectedClip.value.id
    await run(async () => {
      const created = await exportClip(clipId)
      jobId.value = created.id
      job.value = created
      setSelectedClip(await getClip(clipId))
      await loadClips()
    }, '视频切片导出任务已创建', true)
  }

  function download(format: 'csv' | 'json') {
    window.open(exportPublishPlansUrl(format), '_blank')
  }

  async function loadPublishPlans() {
    publishPlans.value = await listPublishPlans()
  }

  async function refreshJob() {
    if (!jobId.value) return
    job.value = await getJob(jobId.value)
  }

  async function queryJob() {
    if (!jobId.value) return
    await run(async () => {
      await refreshJob()
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
    if (tab === 'publish') await run(loadPublishPlans, '发布清单已刷新')
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
    coverTextDraft,
    publishPlans,
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
    deleteVideoRow,
    seek,
    loadClips,
    openClip,
    deleteClipRow,
    submitReview,
    submitPublishPlan,
    saveCoverText,
    submitExportClip,
    download,
    loadPublishPlans,
    refreshJob,
    queryJob,
    retryCurrentJob,
    deleteCurrentJob,
    loadChains,
    changeTab,
  }
}
