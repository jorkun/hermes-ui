
## Windows 支持

### 前置要求

- Python 3.8+
- Node.js 18+
- Rust (安装 Rust: https://rustup.rs/)

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
