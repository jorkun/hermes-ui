#!/usr/bin/env python3
"""
Hermes Bridge Server v0.8 — 支持上下文记忆、图片、项目目录、编码修复
"""

import asyncio
import json
import logging
import os
import sys
import uuid
import base64
from pathlib import Path
from typing import Optional

HERMES_ROOT = Path.home() / ".hermes" / "hermes-agent"
if str(HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT))
os.chdir(str(HERMES_ROOT))

try:
    import uvicorn
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route, WebSocketRoute
    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware
except ImportError as e:
    print(f"缺少依赖：{e}")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("hermes-bridge")

HERMES_HOME = Path.home() / ".hermes"
SESSIONS_DIR = HERMES_HOME / "hermes-gui-sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# 项目目录存储
PROJECTS_DIR = HERMES_HOME / "hermes-projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_MODEL_CONFIGS = {
    "qwen3.6-plus": {"provider": "custom", "api_mode": "anthropic_messages", "base_url": "https://coding.dashscope.aliyuncs.com/apps/anthropic"},
    "qwen-plus": {"provider": "custom", "api_mode": "anthropic_messages", "base_url": "https://coding.dashscope.aliyuncs.com/apps/anthropic"},
    "qwen-turbo": {"provider": "custom", "api_mode": "anthropic_messages", "base_url": "https://coding.dashscope.aliyuncs.com/apps/anthropic"},
    "deepseek-chat": {"provider": "custom", "api_mode": "anthropic_messages", "base_url": "https://api.deepseek.com"},
    "deepseek-reasoner": {"provider": "custom", "api_mode": "anthropic_messages", "base_url": "https://api.deepseek.com"},
    "claude-sonnet-4-20250514": {"provider": "anthropic", "api_mode": None, "base_url": None},
    "claude-opus-4-20250514": {"provider": "anthropic", "api_mode": None, "base_url": None},
}

def read_file(path: str) -> tuple[str, str]:
    try:
        p = Path(os.path.expanduser(os.path.expandvars(path)))
        if not p.exists(): return "", f"不存在：{path}"
        return p.read_text(encoding="utf-8"), ""
    except Exception as e: return "", str(e)

def write_file(path: str, content: str) -> str:
    try:
        p = Path(os.path.expanduser(os.path.expandvars(path)))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return ""
    except Exception as e: return str(e)

def list_files(dir_path: str, pattern: str = "*") -> list:
    """列出目录下的文件"""
    try:
        p = Path(os.path.expanduser(os.path.expandvars(dir_path)))
        if not p.exists(): return []
        return [str(f) for f in p.glob(pattern) if f.is_file()]
    except: return []

def save_project(project_id: str, name: str, path: str) -> str:
    """保存项目配置"""
    config = {"id": project_id, "name": name, "path": path}
    project_file = PROJECTS_DIR / f"{project_id}.json"
    project_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return ""

def load_project(project_id: str) -> Optional[dict]:
    """加载项目配置"""
    project_file = PROJECTS_DIR / f"{project_id}.json"
    if not project_file.exists(): return None
    return json.loads(project_file.read_text(encoding="utf-8"))

def list_projects() -> list:
    """列出所有项目"""
    projects = []
    for f in PROJECTS_DIR.glob("*.json"):
        try:
            projects.append(json.loads(f.read_text(encoding="utf-8")))
        except: pass
    return projects

def delete_project(project_id: str) -> str:
    """删除项目"""
    project_file = PROJECTS_DIR / f"{project_id}.json"
    if project_file.exists():
        project_file.unlink()
        return ""
    return f"项目不存在：{project_id}"

def analyze_code(file_path: str, issue: str) -> str:
    """分析代码问题"""
    content, error = read_file(file_path)
    if error: return f"读取文件失败：{error}"
    
    return f"""文件：{file_path}
问题：{issue}

文件内容:
```
{content}
```

请分析上述代码中的问题并提供修复建议。"""

_agent_cache: dict = {}

def get_agent(model: str, model_config: dict | None = None, session_id: str | None = None):
    cache_key = f"{model}:{session_id or 'default'}"
    
    if cache_key in _agent_cache:
        return _agent_cache[cache_key]

    from run_agent import AIAgent
    from hermes_cli.config import load_config, load_env

    cfg = load_config()
    env = load_env()

    if model_config:
        provider = model_config.get("provider", "custom")
        api_mode = model_config.get("api_mode") or None
        base_url = model_config.get("base_url") or None
        api_key = model_config.get("api_key") or ""
    else:
        model_cfg = DEFAULT_MODEL_CONFIGS.get(model, {})
        provider = model_cfg.get("provider", "custom")
        api_mode = model_cfg.get("api_mode", "anthropic_messages")
        base_url = model_cfg.get("base_url")
        api_key = ""

    if not api_key:
        if provider == "anthropic":
            api_key = env.get("ANTHROPIC_API_KEY", "")
        elif provider in ("custom", "alibaba"):
            api_key = env.get("DASHSCOPE_API_KEY") or env.get("ANTHROPIC_API_KEY") or ""
        elif provider == "openai":
            api_key = env.get("OPENAI_API_KEY", "")

    agent = AIAgent(
        model=model,
        provider=provider,
        api_mode=api_mode,
        base_url=base_url,
        api_key=api_key,
        session_id=session_id,
    )
    _agent_cache[cache_key] = agent
    return agent

async def handle_chat(websocket, path):
    """处理聊天 WebSocket 连接"""
    log.info(f"新聊天连接：{websocket.client}")
    
    current_session_id = None
    current_model = "qwen3.6-plus"
    current_model_config = None
    message_history = []  # 保存当前会话的完整历史
    agent = None
    
    try:
        async for message in websocket.iter_text():
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    continue
                
                if msg_type == "message":
                    content = data.get("content", "")
                    current_model = data.get("model", current_model)
                    current_model_config = data.get("model_config")
                    session_id = data.get("session_id")
                    images = data.get("images", [])  # 图片列表 (base64)
                    
                    if session_id != current_session_id:
                        # 会话变更，清空历史
                        current_session_id = session_id
                        message_history = []
                        agent = None
                    
                    # 获取或创建 Agent
                    if not agent:
                        agent = get_agent(current_model, current_model_config, current_session_id)
                    
                    # 添加用户消息到历史
                    user_msg = {"role": "user", "content": content}
                    if images:
                        # 如果有图片，添加图片到消息
                        user_msg["images"] = images
                    message_history.append(user_msg)
                    
                    log.info(f"收到消息 (会话:{current_session_id}, 历史:{len(message_history)} 条)")
                    
                    # 发送开始标记
                    await websocket.send_text(json.dumps({"type": "start"}))
                    
                    # 构建带上下文的请求
                    response_content = ""
                    try:
                        # 使用完整历史对话调用 Agent
                        # run_conversation 支持 conversation_history 参数
                        log.info(f"调用 Agent (历史：{len(message_history)} 条消息)")
                        
                        # 提取最后一条用户消息
                        current_user_msg = message_history[-1]["content"] if message_history else content
                        
                        # 获取之前的对话历史（不包括最后一条用户消息）
                        prev_history = message_history[:-1] if len(message_history) > 1 else None
                        
                        # 同步调用 run_conversation（在 executor 中运行避免阻塞）
                        loop = asyncio.get_event_loop()
                        
                        def run_agent_sync():
                            try:
                                result = agent.run_conversation(
                                    user_message=current_user_msg,
                                    conversation_history=prev_history,
                                )
                                # 提取响应文本
                                if isinstance(result, dict):
                                    return result.get("response", "") or result.get("assistant_message", "")
                                return str(result) if result else ""
                            except Exception as e:
                                log.error(f"Agent 执行失败：{e}")
                                raise
                        
                        response_content = await loop.run_in_executor(None, run_agent_sync)
                        
                        # 添加助手响应到历史
                        if response_content:
                            message_history.append({"role": "assistant", "content": response_content})
                            
                            # 流式发送响应
                            for i, chunk in enumerate(response_content):
                                await websocket.send_text(json.dumps({"type": "chunk", "content": chunk}))
                                if i % 50 == 0:  # 每 50 个字符发送一次
                                    await asyncio.sleep(0.01)
                        else:
                            log.warning("Agent 返回空响应")
                            await websocket.send_text(json.dumps({"type": "error", "message": "Agent 返回空响应"}))
                        
                    except Exception as e:
                        log.error(f"Agent 调用失败：{e}")
                        await websocket.send_text(json.dumps({"type": "error", "message": f"Agent 错误：{str(e)}"}))
                        continue
                    
                    # 发送完成标记
                    await websocket.send_text(json.dumps({"type": "done"}))
                    
                    # 自动保存会话
                    if current_session_id:
                        session_file = SESSIONS_DIR / f"{current_session_id}.json"
                        session_data = {
                            "id": current_session_id,
                            "model": current_model,
                            "messages": message_history,
                            "updated_at": int(asyncio.get_event_loop().time() * 1000),
                        }
                        session_file.write_text(json.dumps(session_data, indent=2, ensure_ascii=False), encoding="utf-8")
                
                elif msg_type == "interrupt":
                    log.info("用户中断生成")
                    # TODO: 实现中断逻辑
                    
            except json.JSONDecodeError:
                log.error(f"无效 JSON: {message}")
            except Exception as e:
                log.error(f"处理消息失败：{e}")
    
    except Exception as e:
        log.error(f"聊天连接错误：{e}")

async def handle_health(request):
    return JSONResponse({"status": "ok", "version": "0.8.0"})

async def handle_sessions_list(request):
    """获取会话列表"""
    sessions = []
    for f in SESSIONS_DIR.glob("session_*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sessions.append({
                "id": data.get("id"),
                "title": data.get("messages", [{}])[0].get("content", "新会话")[:30],
                "model": data.get("model"),
                "updated_at": data.get("updated_at"),
                "message_count": len(data.get("messages", [])),
            })
        except: pass
    sessions.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
    return JSONResponse({"sessions": sessions})

async def handle_session_get(request):
    """获取会话详情"""
    session_id = request.path_params.get("id")
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        return JSONResponse({"error": "会话不存在"}, status_code=404)
    
    try:
        data = json.loads(session_file.read_text(encoding="utf-8"))
        return JSONResponse({"session": data})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

async def handle_projects_list(request):
    """获取项目列表"""
    return JSONResponse({"projects": list_projects()})

async def handle_project_create(request):
    """创建项目"""
    try:
        data = await request.json()
        project_id = f"proj_{uuid.uuid4().hex[:8]}"
        error = save_project(project_id, data.get("name", "未命名"), data.get("path", ""))
        if error:
            return JSONResponse({"error": error}, status_code=400)
        return JSONResponse({"project": {"id": project_id, "name": data.get("name"), "path": data.get("path")}})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

async def handle_project_delete(request):
    """删除项目"""
    project_id = request.path_params.get("id")
    error = delete_project(project_id)
    if error:
        return JSONResponse({"error": error}, status_code=404)
    return JSONResponse({"success": True})

async def handle_files_list(request):
    """列出项目文件"""
    dir_path = request.query_params.get("path", "")
    pattern = request.query_params.get("pattern", "*")
    if not dir_path:
        return JSONResponse({"error": "需要 path 参数"}, status_code=400)
    return JSONResponse({"files": list_files(dir_path, pattern)})

async def handle_code_analyze(request):
    """分析代码问题"""
    try:
        data = await request.json()
        result = analyze_code(data.get("file_path", ""), data.get("issue", ""))
        return JSONResponse({"analysis": result})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

app = Starlette(
    debug=True,
    routes=[
        WebSocketRoute("/ws/chat", handle_chat),
        Route("/health", handle_health),
        Route("/api/sessions", handle_sessions_list),
        Route("/api/sessions/{id}", handle_session_get),
        Route("/api/projects", handle_projects_list),
        Route("/api/projects", handle_project_create, methods=["POST"]),
        Route("/api/projects/{id}", handle_project_delete, methods=["DELETE"]),
        Route("/api/files", handle_files_list),
        Route("/api/code/analyze", handle_code_analyze, methods=["POST"]),
    ],
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]),
    ],
)

if __name__ == "__main__":
    log.info("Hermes Bridge Server v0.8 启动中...")
    uvicorn.run(app, host="0.0.0.0", port=9120, log_level="info")
