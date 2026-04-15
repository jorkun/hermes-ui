<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <span class="logo-icon">✦</span>
          <span class="logo-text">Hermes</span>
        </div>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/chat" class="nav-item" active-class="active">
          <span class="nav-icon">◈</span>
          <span>聊天</span>
        </router-link>
        <router-link to="/sessions" class="nav-item" active-class="active">
          <span class="nav-icon">◉</span>
          <span>会话</span>
        </router-link>
        <router-link to="/memory" class="nav-item" active-class="active">
          <span class="nav-icon">◇</span>
          <span>记忆</span>
        </router-link>
        <router-link to="/settings" class="nav-item" active-class="active">
          <span class="nav-icon">◎</span>
          <span>设置</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <div class="status-indicator">
          <span class="dot" :class="connected ? 'online' : 'offline'"></span>
          <span class="status-text">{{ connected ? '已连接' : '未连接' }}</span>
        </div>
      </div>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()
const connected = ref(false)

onMounted(async () => {
  try {
    const res = await fetch('/api/status')
    connected.value = res.ok
  } catch {
    connected.value = false
  }
})
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: var(--bg-primary);
}

.sidebar {
  width: 200px;
  min-width: 200px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.sidebar-header {
  padding: 20px 16px;
  border-bottom: 1px solid var(--border);
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  font-size: 20px;
  color: var(--accent);
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 1; text-shadow: 0 0 8px var(--accent); }
  50% { opacity: 0.7; text-shadow: 0 0 2px var(--accent); }
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--text-primary);
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.15s ease;
}

.nav-item:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.nav-item.active {
  background: rgba(124, 106, 247, 0.15);
  color: var(--accent);
}

.nav-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-muted);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.online {
  background: var(--success);
  box-shadow: 0 0 6px var(--success);
}

.dot.offline {
  background: var(--error);
}

.main-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
