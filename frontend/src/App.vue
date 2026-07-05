<script setup lang="ts">
import { watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import AppSidebar from './components/AppSidebar.vue'
import { useVideoOps } from './composables/useVideoOps'
import { provideVideoOps } from './composables/videoOpsContext'
import { isTabKey } from './router'

const ops = useVideoOps()
const route = useRoute()

provideVideoOps(ops)

const { apiKey, statusMessage, saveApiKey, changeTab } = ops

watch(
  () => route.name,
  async (name) => {
    if (isTabKey(name)) await changeTab(name)
  },
  { immediate: true },
)
</script>

<template>
  <el-container class="app-shell">
    <AppSidebar />

    <el-container direction="vertical" class="app-content">
      <AppHeader
        :api-key="apiKey"
        :status-message="statusMessage"
        @update:api-key="apiKey = $event"
        @save-api-key="saveApiKey"
      />

      <el-main class="app-main">
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>
