export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string
  timestamp: number
  tool_calls?: ToolCall[]
  tool_results?: ToolResult[]
  error?: string
}

export interface ToolCall {
  id: string
  name: string
  arguments: string
}

export interface ToolResult {
  call_id: string
  name: string
  output: string
}

export interface ChatSession {
  id: string
  title: string
  created_at: number
  updated_at: number
  message_count: number
  model?: string
}

export interface HermesConfig {
  model: string
  provider: string
  temperature: number
  max_tokens: number
  system_prompt?: string
  dangerously_disable_sleep?: boolean
}

export interface EnvVar {
  key: string
  value: string
  masked: boolean
}

export interface StatusInfo {
  version: string
  model: string
  provider: string
  session_count: number
  tools_count: number
  skills_count: number
}
