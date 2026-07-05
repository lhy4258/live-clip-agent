<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { TabKey } from '../composables/useVideoOps'

const menus: Array<{ key: TabKey; label: string }> = [
  { key: 'videos', label: '视频库' },
  { key: 'clips', label: '切片审核' },
  { key: 'publish', label: '发布清单' },
  { key: 'jobs', label: '任务监控' },
  { key: 'chains', label: 'Chain Runs' },
]

const route = useRoute()
const router = useRouter()

const activeTab = computed(() => (typeof route.name === 'string' ? route.name : 'videos'))

async function handleSelect(key: string) {
  if (key !== activeTab.value) await router.push({ name: key })
}
</script>

<template>
  <el-aside width="224px" class="app-aside">
    <div class="brand">
      <span class="brand-mark">LC</span>
      <div>
        <strong>直播切片 Agent</strong>
        <small>Live Stream Clip</small>
      </div>
    </div>

    <el-menu :default-active="activeTab" class="nav-menu" @select="handleSelect">
      <el-menu-item v-for="item in menus" :key="item.key" :index="item.key">
        <span>{{ item.label }}</span>
      </el-menu-item>
    </el-menu>
  </el-aside>
</template>
