<script setup lang="ts">
defineProps<{
  apiKey: string
  statusMessage: string
}>()

const emit = defineEmits<{
  'update:apiKey': [value: string]
  saveApiKey: []
}>()
</script>

<template>
  <el-header class="app-header">
    <div>
      <h1>直播切片运营后台</h1>
      <p>视频登记、候选切片审核、发布清单与链路追踪</p>
    </div>
    <div class="header-tools">
      <el-input
        :model-value="apiKey"
        placeholder="X-API-Key"
        @update:model-value="emit('update:apiKey', $event)"
        @change="emit('saveApiKey')"
      />
      <el-tag effect="light" type="success">{{ statusMessage }}</el-tag>
    </div>
  </el-header>
</template>
