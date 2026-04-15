<template>
  <div class="memory-page">
    <header class="page-header">
      <h1 class="page-title">长期记忆</h1>
      <div class="header-actions">
        <button class="btn-primary btn-sm" @click="save" :disabled="saving">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </header>
    <div class="memory-content">
      <div class="memory-tabs">
        <button v-for="tab in tabs" :key="tab.key" class="tab-btn" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
          {{ tab.label }}
        </button>
      </div>
      <textarea v-model="content" class="memory-editor" :placeholder="'输入 ' + activeTab + ' 内容...'" spellcheck="false"></textarea>
    </div>
    <p class="save-status" v-if="saveMsg">{{ saveMsg }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const BRIDGE = 'http://localhost:9120'
const tabs = [
  { key: 'MEMORY.md', label: 'MEMORY.md' },
  { key: 'USER.md', label: 'USER.md' },
]

const activeTab = ref('MEMORY.md')
const content = ref('')
const saving = ref(false)
const saveMsg = ref('')

watch(activeTab, loadFile, { immediate: true })

async function loadFile() {
  content.value = ''
  try {
    const res = await fetch(`${BRIDGE}/memory/read?file=${encodeURIComponent(activeTab.value)}`)
    if (res.ok) {
      const data = await res.json()
      content.value = data.content || ''
    }
  } catch {}
}

async function save() {
  saving.value = true
  saveMsg.value = ''
  try {
    const res = await fetch(`${BRIDGE}/memory/write`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file: activeTab.value, content: content.value }),
    })
    saveMsg.value = res.ok ? '✓ 已保存' : '✗ 保存失败'
  } catch {
    saveMsg.value = '✗ 保存失败'
  } finally {
    saving.value = false
    setTimeout(() => saveMsg.value = '', 2000)
  }
}
</script>

<style scoped>
.memory-page { display: flex; flex-direction: column; height: 100%; background: var(--bg-primary); }
.page-header { padding: 24px 32px 16px; border-bottom: 1px solid var(--border); background: var(--bg-secondary); display: flex; align-items: center; justify-content: space-between; }
.page-title { font-size: 20px; font-weight: 700; }
.header-actions { display: flex; gap: 8px; }
.memory-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; padding: 16px; gap: 12px; }
.memory-tabs { display: flex; gap: 4px; }
.tab-btn { padding: 6px 16px; background: transparent; border: 1px solid var(--border); border-radius: 6px; color: var(--text-secondary); font-size: 13px; cursor: pointer; transition: all 0.15s; }
.tab-btn.active { background: rgba(124,106,247,0.15); border-color: var(--accent); color: var(--accent); }
.tab-btn:hover:not(.active) { background: var(--bg-tertiary); }
.memory-editor { flex: 1; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; color: var(--text-primary); font-size: 14px; font-family: 'Geist Mono', monospace; line-height: 1.7; resize: none; outline: none; transition: border-color 0.2s; }
.memory-editor:focus { border-color: var(--accent); }
.save-status { position: fixed; bottom: 20px; right: 20px; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 8px; padding: 8px 16px; font-size: 13px; color: var(--success); }
.btn-primary { padding: 7px 16px; background: var(--accent); color: white; border: none; border-radius: 8px; font-size: 13px; cursor: pointer; }
.btn-primary:hover:not(:disabled) { background: var(--accent-hover); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-sm { padding: 5px 12px; font-size: 12px; }
</style>
