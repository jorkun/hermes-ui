<template>
  <div class="sessions-page">
    <header class="page-header">
      <h1 class="page-title">会话历史</h1>
      <p class="page-desc">{{ sessions.length }} 个会话</p>
    </header>
    <div class="sessions-content">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="sessions.length === 0" class="empty">
        <p>暂无会话记录</p>
      </div>
      <div v-else class="session-list">
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          @click="openSession(s)"
        >
          <div class="session-info">
            <span class="session-title">{{ s.title || '未命名会话' }}</span>
            <span class="session-meta">{{ formatDate(s.updated_at) }} · {{ s.message_count }} 条</span>
          </div>
          <button class="btn-delete" @click.stop="deleteSession(s.id)">×</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import type { ChatSession } from '@/types'

const router = useRouter()
const chatStore = useChatStore()
const sessions = ref<ChatSession[]>([])
const loading = ref(false)

onMounted(loadSessions)

async function loadSessions() {
  loading.value = true
  try {
    const res = await fetch('http://127.0.0.1:9120/api/sessions')
    if (res.ok) {
      const data = await res.json()
      sessions.value = (data.sessions || []).sort((a: ChatSession, b: ChatSession) => b.updated_at - a.updated_at)
    }
  } catch {
    sessions.value = []
  } finally {
    loading.value = false
  }
}

function openSession(s: ChatSession) {
  chatStore.loadSession(s.id).then(() => {
    router.push('/chat')
  })
}

async function deleteSession(id: string) {
  if (!confirm('确定删除此会话？')) return
  try {
    await fetch(`http://127.0.0.1:9120/api/sessions/${id}`, { method: 'DELETE' })
    sessions.value = sessions.value.filter(s => s.id !== id)
  } catch {}
}

function formatDate(ts: number) {
  const d = new Date(ts * 1000)
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.sessions-page { display: flex; flex-direction: column; height: 100%; background: var(--bg-primary); }
.page-header { padding: 24px 32px 16px; border-bottom: 1px solid var(--border); background: var(--bg-secondary); }
.page-title { font-size: 20px; font-weight: 700; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-muted); }
.sessions-content { flex: 1; overflow-y: auto; padding: 16px; }
.session-list { display: flex; flex-direction: column; gap: 8px; }
.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;
}
.session-item:hover { border-color: var(--accent); background: var(--bg-tertiary); }
.session-info { display: flex; flex-direction: column; gap: 4px; }
.session-title { font-size: 14px; font-weight: 500; color: var(--text-primary); }
.session-meta { font-size: 12px; color: var(--text-muted); }
.btn-delete {
  width: 28px; height: 28px;
  border: none; background: transparent;
  color: var(--text-muted); font-size: 18px;
  cursor: pointer; border-radius: 6px;
  transition: all 0.15s;
}
.btn-delete:hover { background: rgba(248,113,113,0.1); color: var(--error); }
.loading, .empty { padding: 40px; text-align: center; color: var(--text-muted); }
</style>
