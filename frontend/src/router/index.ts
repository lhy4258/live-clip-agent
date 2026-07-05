import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import type { TabKey } from '../composables/useVideoOps'
import ChainRunsView from '../views/ChainRunsView.vue'
import ClipReviewView from '../views/ClipReviewView.vue'
import JobMonitorView from '../views/JobMonitorView.vue'
import PublishListView from '../views/PublishListView.vue'
import VideoLibraryView from '../views/VideoLibraryView.vue'

const tabKeys: TabKey[] = ['videos', 'clips', 'publish', 'jobs', 'chains']

export function isTabKey(value: unknown): value is TabKey {
  return typeof value === 'string' && tabKeys.includes(value as TabKey)
}

export const routes: RouteRecordRaw[] = [
  { path: '/', redirect: { name: 'videos' } },
  { path: '/videos', name: 'videos', component: VideoLibraryView },
  { path: '/clips', name: 'clips', component: ClipReviewView },
  { path: '/publish', name: 'publish', component: PublishListView },
  { path: '/jobs', name: 'jobs', component: JobMonitorView },
  { path: '/chains', name: 'chains', component: ChainRunsView },
  { path: '/:pathMatch(.*)*', redirect: { name: 'videos' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
