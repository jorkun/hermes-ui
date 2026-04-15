<template>
  <div class="settings-page">
    <header class="page-header">
      <h1 class="page-title">设置</h1>
      <p class="page-desc">管理 Hermes Agent 配置</p>
    </header>

    <div class="settings-content">
      <!-- Model Config -->
      <section class="settings-section">
        <h3 class="section-title">模型配置</h3>
        <div class="form-grid">
          <div class="form-group">
            <label>当前模型</label>
            <select v-model="config.model" class="select-input" @change="saveConfig">
              <option value="qwen-plus">qwen-plus</option>
              <option value="qwen3.6-plus">qwen3.6-plus</option>
              <option value="qwen3.7-plus">qwen3.7-plus</option>
              <option value="claude-sonnet-4">claude-sonnet-4</option>
              <option value="claude-opus-4">claude-opus-4</option>
              <option value="deepseek-chat">deepseek-chat</option>
              <option value="gpt-4o">gpt-4o</option>
            </select>
          </div>
          <div class="form-group">
            <label>Temperature</label>
            <div class="range-group">
              <input type="range" v-model.number="config.temperature" min="0" max="2" step="0.1" @change="saveConfig" />
              <span class="range-value">{{ config.temperature }}</span>
            </div>
          </div>
          <div class="form-group">
            <label>Max Tokens</label>
            <input type="number" v-model.number="config.max_tokens" class="text-input" @change="saveConfig" />
          </div>
        </div>
      </section>

      <!-- System Prompt -->
      <section class="settings-section">
        <h3 class="section-title">系统提示词</h3>
        <textarea v-model="config.system_prompt" class="textarea-input" rows="5" @blur="saveConfig" placeholder="设置系统提示词..."></textarea>
      </section>

      <!-- Env Vars -->
      <section class="settings-section">
        <div class="section-header">
          <h3 class="section-title">环境变量</h3>
          <button class="btn-primary btn-sm" @click="showAddEnv = true">+ 添加</button>
        </div>
        <div class="env-list">
          <div v-for="env in envVars" :key="env.key" class="env-item">
            <span class="env-key">{{ env.key }}</span>
            <span class="env-value">{{ env.masked ? '••••••••' : env.value }}</span>
            <button class="btn-ghost btn-xs" @click="deleteEnv(env.key)">删除</button>
          </div>
        </div>
      </section>

      <!-- API Status -->
      <section class="settings-section">
        <h3 class="section-title">服务状态</h3>
        <div class="status-grid">
          <div class="status-item">
            <span class="status-label">Hermes API</span>
            <span class="status-value" :class="apiStatus.ok ? 'online' : 'offline'">
              {{ apiStatus.ok ? '运行中' : '离线' }}
            </span>
          </div>
          <div class="status-item">
            <span class="status-label">版本</span>
            <span class="status-value">{{ apiStatus.version || '未知' }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">会话数</span>
            <span class="status-value">{{ apiStatus.session_count || 0 }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">工具数</span>
            <span class="status-value">{{ apiStatus.tools_count || 0 }}</span>
          </div>
        </div>
      </section>

      <!-- Save button -->
      <div class="save-bar">
        <button class="btn-primary" @click="saveConfig">保存配置</button>
        <span v-if="saveMsg" class="save-msg">{{ saveMsg }}</span>
      </div>
    </div>

    <!-- Add Env Modal -->
    <div v-if="showAddEnv" class="modal-overlay" @click.self="showAddEnv = false">
      <div class="modal">
        <h3>添加环境变量</h3>
        <input v-model="newEnvKey" class="text-input" placeholder="KEY" />
        <input v-model="newEnvValue" class="text-input" placeholder="VALUE" type="password" />
        <div class="modal-actions">
          <button class="btn-ghost" @click="showAddEnv = false">取消</button>
          <button class="btn-primary" @click="addEnv">添加</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import type { HermesConfig, EnvVar, StatusInfo } from '@/types'

const config = reactive<HermesConfig>({
  model: 'qwen3.6-plus',
  provider: '',
  temperature: 0.7,
  max_tokens: 8192,
  system_prompt: '',
})

const envVars = ref<EnvVar[]>([])
const apiStatus = ref<StatusInfo>({} as StatusInfo)
const saveMsg = ref('')
const showAddEnv = ref(false)
const newEnvKey = ref('')
const newEnvValue = ref('')

onMounted(async () => {
  await loadStatus()
  await loadConfig()
  await loadEnvVars()
})

async function loadStatus() {
  try {
    const res = await fetch('/api/status')
    if (res.ok) apiStatus.value = await res.json()
  } catch {}
}

async function loadConfig() {
  try {
    const res = await fetch('/api/config')
    if (res.ok) {
      const data = await res.json()
      Object.assign(config, data)
    }
  } catch {}
}

async function loadEnvVars() {
  try {
    const res = await fetch('/api/env')
    if (res.ok) {
      const data = await res.json()
      envVars.value = data.vars || []
    }
  } catch {}
}

async function saveConfig() {
  try {
    await fetch('/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
    saveMsg.value = '✓ 已保存'
    setTimeout(() => saveMsg.value = '', 2000)
  } catch {
    saveMsg.value = '✗ 保存失败'
  }
}

async function addEnv() {
  if (!newEnvKey.value) return
  try {
    await fetch('/api/env', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: newEnvKey.value, value: newEnvValue.value }),
    })
    newEnvKey.value = ''
    newEnvValue.value = ''
    showAddEnv.value = false
    await loadEnvVars()
  } catch {}
}

async function deleteEnv(key: string) {
  try {
    await fetch(`/api/env/${encodeURIComponent(key)}`, { method: 'DELETE' })
    await loadEnvVars()
  } catch {}
}
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
}

.page-header {
  padding: 24px 32px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-secondary);
}

.page-title { font-size: 20px; font-weight: 700; margin-bottom: 4px; }
.page-desc { font-size: 13px; color: var(--text-muted); }

.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.settings-section {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
}

.section-header .section-title { margin-bottom: 0; }

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.text-input, .select-input, .textarea-input {
  background: var(--bg-tertiary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 12px;
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.text-input:focus, .select-input:focus, .textarea-input:focus {
  border-color: var(--accent);
}

.select-input { cursor: pointer; }
.textarea-input { resize: vertical; min-height: 100px; }

.range-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.range-group input[type="range"] {
  flex: 1;
  accent-color: var(--accent);
}

.range-value {
  font-family: 'Geist Mono', monospace;
  font-size: 13px;
  color: var(--accent);
  min-width: 32px;
}

.env-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.env-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.env-key {
  font-family: 'Geist Mono', monospace;
  font-size: 13px;
  color: var(--accent);
  font-weight: 500;
  min-width: 120px;
}

.env-value {
  flex: 1;
  font-size: 13px;
  color: var(--text-secondary);
  font-family: 'Geist Mono', monospace;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px;
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.status-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-muted); }
.status-value { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.status-value.online { color: var(--success); }
.status-value.offline { color: var(--error); }

.save-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
}

.save-msg {
  font-size: 13px;
  color: var(--success);
}

/* Buttons */
.btn-primary {
  padding: 8px 20px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-primary:hover { background: var(--accent-hover); }

.btn-ghost {
  padding: 6px 12px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.btn-ghost:hover { background: var(--bg-tertiary); color: var(--text-primary); }

.btn-sm { padding: 5px 12px; font-size: 12px; }
.btn-xs { padding: 2px 8px; font-size: 11px; border: none; background: transparent; color: var(--error); cursor: pointer; }

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  width: 400px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.modal h3 { font-size: 16px; font-weight: 600; }

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}
</style>
