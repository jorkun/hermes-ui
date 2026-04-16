# Hermes GUI

基于 Tauri + Vue 3 的 Hermes Agent 图形界面客户端。

## 界面预览

![界面预览](./images/image.png)

![界面预览](./images/image2.png)

## 功能特性

### 💬 智能聊天
- 🤖 多模型支持（Qwen、DeepSeek、Claude 等）
- 💬 实时流式对话
- 🖼️ **支持发送图片**（多张图片拖拽上传）
- 🧠 **完整上下文记忆**（会话内自动保存历史对话）
- 📁 **项目目录管理**（添加、切换、管理项目）
- 🔧 **代码分析修复**（选择文件，描述问题，AI 分析）

### 📁 项目管理
- 添加项目目录
- 快速切换项目
- 浏览项目文件
- 文件搜索过滤

### 🔍 代码分析
- 选择项目中的文件
- 描述代码问题
- AI 智能分析并提供修复建议

### 📝 会话管理
- 自动保存会话历史
- 支持多个会话
- 会话间上下文隔离

## 技术栈

- **前端**: Vue 3 + Vite 8 + TypeScript 6 + Pinia 3 + Vue Router 4 + UnoCSS
- **桌面**: Tauri 2
- **后端**: Python (Hermes Bridge v0.8)

## 开发

### 前置要求

- Node.js 22+ (推荐)
- pnpm 9+
- Python 3.8+
- Rust (安装 Rust: https://rustup.rs/)

### 安装依赖

```bash
pnpm install
```

### 开发模式

```bash
pnpm tauri dev
```

### 构建

```bash
pnpm tauri build
```

## 启动 Bridge Server

### macOS / Linux

```bash
cd ~/.hermes/hermes-agent
./venv/bin/python3 server/chat_bridge.py
```

### Windows

```powershell
cd %USERPROFILE%\.hermes\hermes-agent
python server\chat_bridge.py
```

## 项目结构

```
hermes-gui/
├── src/                 # Vue 前端源码
│   ├── pages/          # 页面组件
│   │   ├── ChatPage.vue      # 聊天页面（支持图片、项目、代码分析）
│   │   ├── SessionsPage.vue  # 会话列表
│   │   ├── SettingsPage.vue  # 设置
│   │   └── MemoryPage.vue    # 记忆管理
│   ├── stores/          # Pinia 状态管理
│   │   └── chat.ts      # 聊天 store（图片、项目、代码分析 API）
│   └── ...
├── server/             # Bridge Server
│   └── chat_bridge.py  # WebSocket 桥接服务（v0.8）
├── images/             # 文档图片
└── src-tauri/          # Tauri 桌面应用
```

## 配置

首次使用需要在 Bridge Server 中配置 API Key：

```bash
# 设置环境变量
export DASHSCOPE_API_KEY=your_key  # 阿里云百炼
export ANTHROPIC_API_KEY=your_key  # Claude
```

## 使用指南

### 1. 发送图片
1. 点击输入框左侧的 🖼️ 按钮
2. 选择一张或多张图片
3. 图片会显示在预览区域
4. 输入消息后发送

### 2. 管理项目
1. 点击顶部 📁 按钮
2. 点击"+ 添加项目"
3. 输入项目名称和路径（或点击"选择"按钮浏览目录）
4. 点击项目卡片切换当前项目

### 3. 代码分析
1. 点击顶部 📁 按钮
2. 在当前项目文件列表中点击文件
3. 描述代码问题
4. 点击"分析"获取 AI 建议

## Windows 支持

### 构建步骤

```powershell
# 安装依赖
pnpm install

# 开发模式
pnpm tauri dev

# 构建 Windows 安装包
pnpm tauri build
```

构建产物位于 `src-tauri/target/release/bundle/`:
- MSI 安装包
- NSIS 安装程序 (.exe)

### 启动 Bridge Server (Windows)

```powershell
# 方法 1: 使用启动脚本
cd server
.\start_bridge.bat

# 方法 2: 手动启动
cd %USERPROFILE%\.hermes\hermes-agent
python server\chat_bridge.py
```

## API 端点

Bridge Server v0.8 提供以下 API：

- `GET /health` - 健康检查
- `WebSocket /ws/chat` - 聊天 WebSocket
- `GET /api/sessions` - 获取会话列表
- `GET /api/sessions/{id}` - 获取会话详情
- `PUT /api/sessions/{id}` - 保存会话
- `GET /api/projects` - 获取项目列表
- `POST /api/projects` - 创建项目
- `DELETE /api/projects/{id}` - 删除项目
- `GET /api/files?path=xxx&pattern=xxx` - 列出文件
- `POST /api/code/analyze` - 分析代码问题

## 更新日志

### v0.8.0 (2026-04-16)
- ✨ 支持发送图片（多图片上传）
- ✨ 完整上下文记忆（会话内历史对话自动保存）
- ✨ 项目目录管理（添加、切换、删除项目）
- ✨ 代码分析功能（AI 辅助代码修复）
- ✨ 文件浏览器（搜索、过滤项目文件）
- 🐛 修复会话上下文丢失问题
- 🐛 优化 Bridge 连接稳定性

### v0.7.0 (2026-04-15)
- 添加自定义模型支持
- 添加 API Key 配置
- 会话管理功能

## License

MIT License - 详见 [LICENSE](LICENSE)
