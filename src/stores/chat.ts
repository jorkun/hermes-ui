import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Message } from '@/types'

const WS_URL = 'ws://127.0.0.1:9120/ws/chat'
const HTTP_URL = 'http://127.0.0.1:9120'

const DEFAULT_MODELS = [
  { id: 'qwen3.6-plus', name: 'Qwen 3.6 Plus', provider: 'custom', api_mode: 'anthropic_messages', base_url: 'https://coding.dashscope.aliyuncs.com/apps/anthropic', api_key: '' },
  { id: 'qwen-plus', name: 'Qwen Plus', provider: 'custom', api_mode: 'anthropic_messages', base_url: 'https://coding.dashscope.aliyuncs.com/apps/anthropic', api_key: '' },
  { id: 'qwen-turbo', name: 'Qwen Turbo', provider: 'custom', api_mode: 'anthropic_messages', base_url: 'https://coding.dashscope.aliyuncs.com/apps/anthropic', api_key: '' },
  { id: 'deepseek-chat', name: 'DeepSeek Chat', provider: 'custom', api_mode: 'anthropic_messages', base_url: 'https://api.deepseek.com', api_key: '' },
  { id: 'deepseek-reasoner', name: 'DeepSeek Reasoner', provider: 'custom', api_mode: 'anthropic_messages', base_url: 'https://api.deepseek.com', api_key: '' },
  { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4', provider: 'anthropic', api_mode: '', base_url: '', api_key: '' },
  { id: 'claude-opus-4-20250514', name: 'Claude Opus 4', provider: 'anthropic', api_mode: '', base_url: '', api_key: '' }
]

export interface ModelConfig {
  id: string
  name: string
  provider: string
  api_mode: string
  base_url: string
  api_key: string
}

export interface SessionData {
  id: string
  title: string
  model: string
  messages: Message[]
  created_at: number
  updated_at: number
}

export interface ProjectConfig {
  id: string
  name: string
  path: string
}

export interface FileItem {
  path: string
  name: string
  type: 'file' | 'directory'
}

// 检查 Bridge 是否运行
async function checkBridge(): Promise<boolean> {
  try {
    const res = await fetch(`${HTTP_URL}/health`, { method: 'GET' })
    return res.ok
  } catch {
    return false
  }
}

// 会话存储 API
async function saveSession(session: SessionData): Promise<void> {
  try {
    await fetch(`${HTTP_URL}/api/sessions/${session.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(session)
    })
  } catch (e) { console.error('保存会话失败', e) }
}

async function loadSessionFromServer(sessionId: string): Promise<SessionData | null> {
  try {
    const res = await fetch(`${HTTP_URL}/api/sessions/${sessionId}`)
    if (res.ok) {
      const data = await res.json()
      return data.session
    }
  } catch (e) { console.error('加载会话失败', e) }
  return null
}

// 项目 API
async function loadProjects(): Promise<ProjectConfig[]> {
  try {
    const res = await fetch(`${HTTP_URL}/api/projects`)
    if (res.ok) {
      const data = await res.json()
      return data.projects || []
    }
  } catch (e) { console.error('加载项目失败', e) }
  return []
}

async function createProject(name: string, path: string): Promise<ProjectConfig | null> {
  try {
    const res = await fetch(`${HTTP_URL}/api/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, path })
    })
    if (res.ok) {
      const data = await res.json()
      return data.project
    }
  } catch (e) { console.error('创建项目失败', e) }
  return null
}

async function deleteProject(projectId: string): Promise<boolean> {
  try {
    const res = await fetch(`${HTTP_URL}/api/projects/${projectId}`, { method: 'DELETE' })
    return res.ok
  } catch (e) { console.error('删除项目失败', e) }
  return false
}

async function loadFiles(dirPath: string, pattern: string = '*'): Promise<FileItem[]> {
  try {
    const res = await fetch(`${HTTP_URL}/api/files?path=${encodeURIComponent(dirPath)}&pattern=${encodeURIComponent(pattern)}`)
    if (res.ok) {
      const data = await res.json()
      return data.files || []
    }
  } catch (e) { console.error('加载文件失败', e) }
  return []
}

async function analyzeCode(filePath: string, issue: string): Promise<string> {
  try {
    const res = await fetch(`${HTTP_URL}/api/code/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_path: filePath, issue })
    })
    if (res.ok) {
      const data = await res.json()
      return data.analysis || ''
    }
  } catch (e) { console.error('分析代码失败', e) }
  return ''
}

// 图片转 base64
function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const currentSessionId = ref<string | null>(null)
  const connected = ref(false)
  const loading = ref(false)
  const connectionError = ref<string | null>(null)
  const bridgeStatus = ref<'checking' | 'online' | 'offline'>('checking')

  const availableModels = ref<ModelConfig[]>([...DEFAULT_MODELS])
  const currentModel = ref('qwen3.6-plus')
  
  // 项目相关
  const projects = ref<ProjectConfig[]>([])
  const currentProject = ref<ProjectConfig | null>(null)
  const projectFiles = ref<FileItem[]>([])
  
  // 图片相关
  const pendingImages = ref<Array<{ file: File, base64: string }>>([])

  let ws: WebSocket | null = null
  let msgId = 0
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let pingTimer: ReturnType<typeof setInterval> | null = null
  let checkInterval: ReturnType<typeof setInterval> | null = null

  function loadCustomModels() {
    try {
      const saved = localStorage.getItem('hermes-custom-models')
      if (saved) {
        const customs = JSON.parse(saved) as ModelConfig[]
        availableModels.value = [...DEFAULT_MODELS, ...customs]
      }
    } catch (e) { console.error('加载自定义模型失败', e) }
  }

  function saveCustomModels() {
    const customs = availableModels.value.filter(m => !DEFAULT_MODELS.find(d => d.id === m.id))
    localStorage.setItem('hermes-custom-models', JSON.stringify(customs))
  }

  function addCustomModel(config: Omit<ModelConfig, 'id'>) {
    const id = `custom-${Date.now()}`
    availableModels.value.push({ ...config, id })
    saveCustomModels()
    return id
  }

  function removeCustomModel(id: string) {
    const idx = availableModels.value.findIndex(m => m.id === id)
    if (idx > -1 && !DEFAULT_MODELS.find(d => d.id === id)) {
      availableModels.value.splice(idx, 1)
      saveCustomModels()
      if (currentModel.value === id) {
        currentModel.value = 'qwen3.6-plus'
      }
    }
  }

  // 加载项目列表
  async function loadProjectsList() {
    projects.value = await loadProjects()
  }

  // 添加项目
  async function addProject(name: string, path: string) {
    const project = await createProject(name, path)
    if (project) {
      projects.value.push(project)
      return project
    }
    return null
  }

  // 删除项目
  async function removeProject(projectId: string) {
    const success = await deleteProject(projectId)
    if (success) {
      projects.value = projects.value.filter(p => p.id !== projectId)
      if (currentProject.value?.id === projectId) {
        currentProject.value = null
      }
    }
  }

  // 选择项目
  function selectProject(project: ProjectConfig) {
    currentProject.value = project
  }

  // 加载项目文件
  async function loadProjectFiles(dirPath: string, pattern: string = '*') {
    projectFiles.value = await loadFiles(dirPath, pattern)
    return projectFiles.value
  }

  // 分析代码
  async function analyzeCodeIssue(filePath: string, issue: string) {
    return await analyzeCode(filePath, issue)
  }

  // 添加图片
  async function addImage(file: File) {
    const base64 = await fileToBase64(file)
    pendingImages.value.push({ file, base64 })
  }

  // 移除图片
  function removeImage(index: number) {
    pendingImages.value.splice(index, 1)
  }

  // 清空图片
  function clearImages() {
    pendingImages.value = []
  }

  // 定期检查 Bridge 状态
  function startBridgeCheck() {
    if (checkInterval) clearInterval(checkInterval)
    checkBridge().then(ok => {
      bridgeStatus.value = ok ? 'online' : 'offline'
      if (!ok) {
        connectionError.value = 'Bridge 未连接'
      }
    })
    checkInterval = setInterval(async () => {
      const ok = await checkBridge()
      bridgeStatus.value = ok ? 'online' : 'offline'
      if (ok && !connected.value && !ws) {
        connect().catch(() => {})
      }
    }, 5000)
  }

  function connect(): Promise<void> {
    return new Promise(async (resolve, reject) => {
      const bridgeOk = await checkBridge()
      if (!bridgeOk) {
        bridgeStatus.value = 'offline'
        connectionError.value = 'Bridge 未启动，请先启动 Bridge'
        reject(new Error('Bridge 未启动'))
        return
      }
      bridgeStatus.value = 'online'

      if (ws && ws.readyState === WebSocket.OPEN) { resolve(); return }
      if (ws) { ws.close(); ws = null }

      connectionError.value = null
      console.log('[Chat] 正在连接 Bridge...')
      ws = new WebSocket(WS_URL)

      const timeout = setTimeout(() => {
        connectionError.value = '连接超时'
        reject(new Error('连接超时'))
        ws?.close()
      }, 10000)

      ws.onopen = () => {
        clearTimeout(timeout)
        connected.value = true
        connectionError.value = null
        console.log('[Chat] WebSocket 已连接', ws?.readyState)
        if (pingTimer) clearInterval(pingTimer)
        pingTimer = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }))
          }
        }, 30000)
        resolve()
      }
      ws.onmessage = (e) => {
        try {
          const d = JSON.parse(e.data)
          if (d.type === 'start') {
            messages.value.push({ id: `msg_${++msgId}`, role: 'assistant', content: '', timestamp: Date.now() })
          } else if (d.type === 'chunk') {
            const last = messages.value[messages.value.length - 1]
            if (last?.role === 'assistant') last.content += d.content
            else messages.value.push({ id: `msg_${++msgId}`, role: 'assistant', content: d.content, timestamp: Date.now() })
          } else if (d.type === 'error') {
            const last = messages.value[messages.value.length - 1]
            if (last?.role === 'assistant') last.error = d.message
            else messages.value.push({ id: `msg_${++msgId}`, role: 'assistant', content: '', timestamp: Date.now(), error: d.message })
            loading.value = false
          } else if (d.type === 'done') {
            loading.value = false
            if (currentSessionId.value) {
              saveSession({
                id: currentSessionId.value,
                title: _getSessionTitle(),
                model: currentModel.value,
                messages: messages.value.map(m => ({ id: m.id, role: m.role, content: m.content, timestamp: m.timestamp })),
                created_at: Date.now(),
                updated_at: Date.now(),
              })
            }
          } else if (d.type === 'info') {
            loading.value = false
          } else if (d.type === 'pong') {
            // ping 响应
          }
        } catch (err) {
          console.error('[Chat] 解析消息失败:', err)
        }
      }
      ws.onclose = (e) => {
        clearTimeout(timeout)
        connected.value = false
        connectionError.value = `连接断开 (${e.code})`
        console.log('[Chat] WebSocket 已断开', e)
        if (pingTimer) {
          clearInterval(pingTimer)
          pingTimer = null
        }
        if (!reconnectTimer) {
          reconnectTimer = setTimeout(() => {
            reconnectTimer = null
            connect().catch(() => {})
          }, 3000)
        }
      }
      ws.onerror = (e) => {
        clearTimeout(timeout)
        connected.value = false
        connectionError.value = '连接失败'
        console.error('[Chat] WebSocket 错误', e)
        reject(new Error('WebSocket 连接失败'))
      }
    })
  }

  async function sendMessage(text: string) {
    if (loading.value) return
    
    const userMsg = { 
      id: `msg_${++msgId}`, 
      role: 'user' as const, 
      content: text, 
      timestamp: Date.now(),
      images: pendingImages.value.length > 0 ? pendingImages.value.map(img => img.base64) : undefined
    }
    messages.value.push(userMsg)
    loading.value = true
    
    try {
      await connect()
      const modelCfg = availableModels.value.find(m => m.id === currentModel.value)
      ws!.send(JSON.stringify({
        type: 'message',
        content: text,
        model: currentModel.value,
        model_config: modelCfg,
        session_id: currentSessionId.value,
        images: pendingImages.value.length > 0 ? pendingImages.value.map(img => img.base64) : [],
      }))
      
      // 发送后清空图片
      clearImages()
    } catch (e: any) {
      loading.value = false
      connectionError.value = e.message
      messages.value.push({ id: `msg_${++msgId}`, role: 'assistant', content: '', timestamp: Date.now(), error: `连接失败：${e.message}` })
    }
  }

  function setModel(modelId: string) {
    currentModel.value = modelId
    messages.value = []
    currentSessionId.value = null
  }

  function interrupt() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'interrupt' }))
    }
  }

  function clearMessages() { messages.value = [] }
  function newSession() { currentSessionId.value = null; messages.value = [] }

  function _getSessionTitle(): string {
    const firstUserMsg = messages.value.find(m => m.role === 'user')
    if (firstUserMsg) {
      const title = firstUserMsg.content.slice(0, 30)
      return firstUserMsg.content.length > 30 ? title + '...' : title
    }
    return '新会话'
  }

  async function loadSession(sessionId: string) {
    const session = await loadSessionFromServer(sessionId)
    if (session) {
      currentSessionId.value = session.id
      currentModel.value = session.model || 'qwen3.6-plus'
      messages.value = session.messages.map(m => ({
        ...m,
        id: m.id || `msg_${++msgId}`
      }))
    }
  }

  function createSession() {
    currentSessionId.value = `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    messages.value = []
  }

  createSession()
  loadCustomModels()
  startBridgeCheck()
  loadProjectsList()

  return {
    messages,
    currentSessionId,
    connected,
    loading,
    connectionError,
    bridgeStatus,
    availableModels,
    currentModel,
    projects,
    currentProject,
    projectFiles,
    pendingImages,
    addCustomModel,
    removeCustomModel,
    sendMessage,
    setModel,
    connect,
    interrupt,
    clearMessages,
    newSession,
    loadSession,
    createSession,
    loadProjectsList,
    addProject,
    removeProject,
    selectProject,
    loadProjectFiles,
    analyzeCodeIssue,
    addImage,
    removeImage,
    clearImages,
  }
})
