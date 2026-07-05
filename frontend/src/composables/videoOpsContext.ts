import { inject, provide, type InjectionKey } from 'vue'
import type { useVideoOps } from './useVideoOps'

export type VideoOpsContext = ReturnType<typeof useVideoOps>

const videoOpsKey: InjectionKey<VideoOpsContext> = Symbol('videoOps')

export function provideVideoOps(context: VideoOpsContext) {
  provide(videoOpsKey, context)
}

export function useVideoOpsContext() {
  const context = inject(videoOpsKey)
  if (!context) throw new Error('videoOps context is not provided')
  return context
}
