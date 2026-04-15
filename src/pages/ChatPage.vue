<template>
  <div class="chat-page">
    <header class="chat-header">
      <div class="header-left">
        <h2 class="chat-title">聊天</h2>
        <div class="model-selector">
          <select v-model="selectedModel" class="model-select" @change="onModelChange">
            <option v-for="m in availableModels" :key="m.id" :value="m.id">
              {{ m.name }}{{ isCustomModel(m.id) ? ' ✎' : '' }}
            </option>
          </select>
          <button class="btn-add-model" @click="showAddModel = true" title="添加自定义模型">+</button>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn-ghost icon-btn" @click="clearChat" title="清空">⊗</button>
        <button class="btn-ghost icon-btn" @click="newSession" title="新会话">＋</button>
      </div>
    </header>

    <!-- 添加模型弹窗 -->
    <div v-if="showAddModel" class="modal-overlay" @click.self="showAddModel = false">
      <div class="modal">
        <div class="modal-header">
          <h3>添加自定义模型</h3>
          <button class="btn-close" @click="showAddModel = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>模型名称</label>
            <input v-model="newModel.name" placeholder="如: My Custom Model" />
          </div>
          <div class="form-group">
            <label>模型 ID</label>
            <input v-model="newModel.id" placeholder="如: custom-gpt-4" />
          </div>
          <div class="form-group">
            <label>Provider</label>
            <select v-model="newModel.provider">
              <option value="custom">Custom (通用)</option>
              <option value="anthropic">Anthropic</option>
              <option value="openai">OpenAI</option>
              <option value="deepseek">DeepSeek</option>
              <option value="alibaba">Alibaba (百炼)</option>
            </select>
          </div>
          <div class="form-group" v-if="newModel.provider === 'custom'">
            <label>API Mode</label>
            <select v-model="newModel.api_mode">
              <option value="anthropic_messages">anthropic_messages</option>
              <option value="openai">openai</option>
            </select>
          </div>
          <div class="form-group" v-if="newModel.provider === 'custom'">
            <label>Base URL</label>
            <input v-model="newModel.base_url" placeholder="https://api.example.com/v1" />
          </div>
          <div class="form-group">
            <label>API Key (可选，默认使用环境变量)</label>
            <input v-model="newModel.api_key" type="password" placeholder="sk-xxx 或 qwen-xxx" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showAddModel = false">取消</button>
          <button class="btn-primary" @click="addModel" :disabled="!newModel.name || !newModel.id">添加</button>
        </div>
      </div>
    </div>

    <div class="messages-container" ref="messagesRef">
      <div v-if="messages.length === 0" class="empty-state">
        <div class="empty-icon">◈</div>
        <p class="empty-title">开始对话</p>
        <p class="empty-desc">发送消息与 Hermes Agent 交流</p>
        <!-- 显示连接状态 -->
        <p v-if="!connected" class="connection-error">⚠️ Bridge 未连接，请确保 App 正常启动</p>
      </div>

      <div v-for="msg in messages" :key="msg.id" class="message-wrapper">
        <div v-if="msg.role === 'user'" class="message user-message">
          <div class="message-avatar user-avatar">U</div>
          <div class="message-content">
            <div class="message-text">{{ msg.content }}</div>
          </div>
        </div>
        <div v-else class="message assistant-message">
          <div class="message-avatar bot-avatar">H</div>
          <div class="message-content">
            <div v-if="msg.error" class="message-error">{{ msg.error }}</div>
            <div v-else class="message-text">{{ msg.content || '...' }}</div>
          </div>
        </div>
      </div>

      <div v-if="loading" class="message-wrapper">
        <div class="message assistant-message">
          <div class="message-avatar bot-avatar">H</div>
          <div class="message-content">
            <div class="typing-indicator"><span></span><span></span><span></span></div>
          </div>
        </div>
      </div>
    </div>

    <div class="input-area">
      <div class="input-container">
        <textarea
          ref="inputRef"
          v-model="inputText"
          class="chat-input"
          placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
          rows="1"
          @keydown="handleKeydown"
          @input="autoResize"
        ></textarea>
        <button class="send-btn" :disabled="(!inputText.trim() && !loading)" @click="loading ? stopGeneration() : send()">
          <span class="send-icon">{{ loading ? '◼' : '↑' }}</span>
        </button>
      </div>
      <p class="input-hint">{{ currentModelName }} · {{ connected ? '已连接' : 'Bridge 连接中...' }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, reactive, onUnmounted } from 'vue'
import { useChatStore } from '@/stores/chat'

const store = useChatStore()
const messagesRef = ref<HTMLElement>()
const inputRef = ref<HTMLTextAreaElement>()
const inputText = ref('')
const showAddModel = ref(false)
const newModel = reactive({
  name: '',
  id: '',
  provider: 'custom',
  api_mode: 'anthropic_messages',
  base_url: '',
  api_key: '',
})

const messages = computed(() => store.messages)
const loading = computed(() => store.loading)
const connected = computed(() => store.connected)
const availableModels = computed(() => store.availableModels)
const selectedModel = computed({
  get: () => store.currentModel,
  set: (v) => store.setModel(v),
})
const currentModelName = computed(() => {
  const m = store.availableModels.find(x => x.id === store.currentModel)
  return m?.name || store.currentModel
})

function isCustomModel(id: string) {
  return id.startsWith('custom-')
}

function onModelChange() {}

function addModel() {
  if (!newModel.name || !newModel.id) return
  store.addCustomModel({
    name: newModel.name,
    id: newModel.id,
    provider: newModel.provider,
    api_mode: newModel.api_mode,
    base_url: newModel.base_url,
    api_key: newModel.api_key,
  })
  store.setModel(newModel.id)
  // 重置
  newModel.name = ''
  newModel.id = ''
  newModel.provider = 'custom'
  newModel.api_mode = 'anthropic_messages'
  newModel.base_url = ''
  newModel.api_key = ''
  showAddModel.value = false
}

async function send() {
  const text = inputText.value.trim()
  if (!text || loading.value) return
  inputText.value = ''
  if (inputRef.value) inputRef.value.style.height = 'auto'
  await store.sendMessage(text)
  scrollToBottom()
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

function autoResize() {
  const el = inputRef.value
  if (el) {
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 200) + 'px'
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

function clearChat() { store.clearMessages() }
function newSession() { store.createSession() }

onMounted(() => { 
  inputRef.value?.focus()
  // 尝试连接
  store.connect().catch(() => {})
})

onUnmounted(() => {
  // 清理
})
</script>

<style scoped>
.chat-page { display: flex; flex-direction: column; height: 100%; background: var(--bg-primary); }
.chat-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 24px; border-bottom: 1px solid var(--border); background: var(--bg-secondary); flex-shrink: 0; }
.header-left { display: flex; align-items: center; gap: 12px; }
.chat-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.model-selector { display: flex; gap: 4px; }
.model-select { padding: 6px 12px; border-radius: 8px 0 0 8px; border: 1px solid var(--border); border-right: none; background: var(--bg-tertiary); color: var(--text-primary); font-size: 13px; cursor: pointer; min-width: 140px; }
.model-select:focus { outline: none; border-color: var(--accent); }
.btn-add-model { width: 32px; height: 32px; border-radius: 0 8px 8px 0; border: 1px solid var(--border); background: var(--bg-tertiary); color: var(--text-secondary); font-size: 16px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.btn-add-model:hover { background: var(--accent); color: white; border-color: var(--accent); }
.header-actions { display: flex; gap: 4px; }
.icon-btn { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: transparent; border: 1px solid var(--border); border-radius: 8px; color: var(--text-secondary); cursor: pointer; }
.icon-btn:hover { background: var(--bg-tertiary); color: var(--text-primary); }

.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal { background: var(--bg-secondary); border-radius: 16px; width: 90%; max-width: 420px; border: 1px solid var(--border); }
.modal-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--border); }
.modal-header h3 { font-size: 16px; font-weight: 600; color: var(--text-primary); margin: 0; }
.btn-close { width: 28px; height: 28px; border: none; background: transparent; color: var(--text-secondary); font-size: 20px; cursor: pointer; border-radius: 6px; }
.btn-close:hover { background: var(--bg-tertiary); }
.modal-body { padding: 20px; display: flex; flex-direction: column; gap: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 13px; color: var(--text-secondary); font-weight: 500; }
.form-group input, .form-group select { padding: 10px 12px; border-radius: 8px; border: 1px solid var(--border); background: var(--bg-tertiary); color: var(--text-primary); font-size: 14px; }
.form-group input:focus, .form-group select:focus { outline: none; border-color: var(--accent); }
.modal-footer { padding: 16px 20px; border-top: 1px solid var(--border); display: flex; justify-content: flex-end; gap: 8px; }
.btn-secondary { padding: 8px 16px; border-radius: 8px; border: 1px solid var(--border); background: transparent; color: var(--text-primary); font-size: 14px; cursor: pointer; }
.btn-primary { padding: 8px 16px; border-radius: 8px; border: none; background: var(--accent); color: white; font-size: 14px; cursor: pointer; }
.btn-primary:hover:not(:disabled) { opacity: 0.9; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

.messages-container { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; }
.empty-state { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 60px 20px; }
.empty-icon { font-size: 48px; color: var(--accent); opacity: 0.6; margin-bottom: 16px; }
.empty-title { font-size: 18px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.empty-desc { font-size: 14px; color: var(--text-muted); }
.connection-error { font-size: 13px; color: #f59e0b; margin-top: 12px; padding: 8px 16px; background: rgba(245,158,11,0.1); border-radius: 8px; }
.message-wrapper { display: flex; }
.message { display: flex; gap: 12px; max-width: 85%; }
.user-message { margin-left: auto; flex-direction: row-reverse; }
.message-avatar { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; flex-shrink: 0; }
.user-avatar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
.bot-avatar { background: linear-gradient(135deg, var(--accent) 0%, #a855f7 100%); color: white; }
.message-content { flex: 1; min-width: 0; }
.message-text { padding: 12px 16px; border-radius: 12px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
.user-message .message-text { background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%); border: 1px solid #667eea44; color: var(--text-primary); border-radius: 12px 12px 4px 12px; }
.assistant-message .message-text { background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 12px 12px 12px 4px; }
.message-error { padding: 12px 16px; background: rgba(248,113,113,0.1); border: 1px solid rgba(248,113,113,0.3); border-radius: 12px; color: var(--error); font-size: 13px; }
.typing-indicator { display: flex; gap: 4px; padding: 4px 0; }
.typing-indicator span { width: 8px; height: 8px; background: var(--accent); border-radius: 50%; animation: typing-bounce 1.4s ease-in-out infinite; }
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
@keyframes typing-bounce { 0%,60%,100% { transform: translateY(0); opacity: 0.4; } 30% { transform: translateY(-6px); opacity: 1; } }
.input-area { padding: 16px 24px 12px; border-top: 1px solid var(--border); background: var(--bg-secondary); flex-shrink: 0; }
.input-container { display: flex; gap: 12px; align-items: flex-end; background: var(--bg-tertiary); border: 1px solid var(--border); border-radius: 12px; padding: 8px 8px 8px 16px; transition: border-color 0.2s; }
.input-container:focus-within { border-color: var(--accent); }
.chat-input { flex: 1; background: transparent; border: none; outline: none; color: var(--text-primary); font-size: 14px; font-family: inherit; line-height: 1.5; resize: none; min-height: 24px; max-height: 200px; padding: 4px 0; }
.chat-input::placeholder { color: var(--text-muted); }
.send-btn { width: 40px; height: 40px; border-radius: 10px; border: none; background: var(--accent); color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.send-btn:hover:not(:disabled) { background: var(--accent-hover); }
.send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.send-icon { font-size: 18px; font-weight: 600; }
.input-hint { margin-top: 8px; font-size: 11px; color: var(--text-muted); text-align: center; }
</style>
