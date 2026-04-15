#!/usr/bin/env python3
"""
Hermes Bridge Server v0.7 — 支持自定义 API Key
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from pathlib import Path

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
    print(f"缺少依赖: {e}")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("hermes-bridge")

HERMES_HOME = Path.home() / ".hermes"
SESSIONS_DIR = HERMES_HOME / "hermes-gui-sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

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
        if not p.exists(): return "", f"不存在: {path}"
        return p.read_text(encoding="utf-8"), ""
    except Exception as e: return "", str(e)

def write_file(path: str, content: str) -> str:
    try:
        p = Path(os.path.expanduser(os.path.expandvars(path)))
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return ""
    except Exception as e: return str(e)

_agent_cache: dict = {}

def get_agent(model: str, model_config: dict | None = None, session_id: str | None = None):
    cache_key = f"{model}:{session_id or 'default'}"
    
    if cache_key in _agent_cache:
        return _agent_cache[cache_key]

    from run_agent import AIAgent
    from hermes_cli.config import load_config, load_env

    cfg = load_config()
    env = load_env()

    # 使用传入的配置或默认值
    if model_config:
        provider = model_config.get("provider", "custom")
        api_mode = model_config.get("api_mode") or None
        base_url = model_config.get("base_url") or None
        # 优先使用传入的 api_key，否则使用环境变量
        api_key = model_config.get("api_key") or ""
    else:
        model_cfg = DEFAULT_MODEL_CONFIGS.get(model, {})
        provider = model_cfg.get("provider", "custom")
        api_mode = model_cfg.get("api_mode", "anthropic_messages")
        base_url = model_cfg.get("base_url")
        api_key = ""

    # 如果没有传入 api_key，尝试从环境变量获取
    if not api_key:
        if provider == "anthropic":
            api_key = env.get("ANTHROPIC_API_KEY", "")
        elif provider in ("custom", "alibaba"):
            api_key = env.get("DASHSCOPE_API_KEY") or env.get("ANTHROPIC_API_KEY") or ""
        elif provider == "openai":
            api_key = env.get("OPENAI_API_KEY", "")
        elif provider == "deepseek":
            api_key = env.get("DEEPSEEK_API_KEY") or env.get("OPENAI_API_KEY", "")
    
    if not api_key:
        log.warning(f"[Agent] 未找到 API Key for provider: {provider}")

    kwargs = {
        "model": model,
        "provider": provider,
        "max_tokens": 8192,
    }
    if api_mode:
        kwargs["api_mode"] = api_mode
    if base_url:
        kwargs["base_url"] = base_url
    if api_key:
        kwargs["api_key"] = api_key

    has_key_flag = bool(api_key)
    log.info(f"Agent: model={model}, provider={provider}, api_mode={api_mode}, base_url={base_url}, has_key={has_key_flag}")
    
    try:
        agent = AIAgent(**kwargs)
    except Exception as e:
        log.error(f"创建 Agent 失败: {e}")
        raise

    if session_id:
        agent.session_id = session_id
    _agent_cache[cache_key] = agent
    return agent

async def ws_chat_endpoint(websocket):
    cid = str(uuid.uuid4())[:8]
    log.info(f"[{cid}] WS 连接 from {websocket.client}")
    await websocket.accept()
    agent, session_id, current_model, current_config = None, None, None, None
    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            t = msg.get("type")
            content = msg.get("content", "").strip()
            session_id = msg.get("session_id") or session_id
            current_model = msg.get("model") or current_model or "qwen3.6-plus"
            current_config = msg.get("model_config") or current_config

            if t == "message" and content:
                try:
                    agent = get_agent(current_model, current_config, session_id)
                    log.info(f"[{cid}] → model={current_model}, has_config={current_config is not None}")
                    result = agent.run_conversation(
                        user_message=content,
                        conversation_history=[],
                        task_id=session_id or str(uuid.uuid4()),
                    )
                    err = result.get("error")
                    text = result.get("final_response", "")

                    if err:
                        await websocket.send_json({"type": "error", "message": str(err)[:500]})
                    elif text:
                        await websocket.send_json({"type": "start"})
                        for i in range(0, len(text), 10):
                            await websocket.send_json({"type": "chunk", "content": text[i:i+10]})
                            await asyncio.sleep(0.01)
                        await websocket.send_json({"type": "done"})
                        session_id = result.get("session_id") or result.get("task_id") or session_id
                    else:
                        await websocket.send_json({"type": "error", "message": "无响应返回"})
                except Exception as e:
                    log.exception(f"[{cid}] Agent 错误")
                    await websocket.send_json({"type": "error", "message": str(e)[:300]})

            elif t == "ping":
                await websocket.send_json({"type": "pong"})
            elif t == "interrupt":
                if agent:
                    try:
                        agent.interrupt()
                        await websocket.send_json({"type": "info", "message": "已中断"})
                    except Exception:
                        pass
    except Exception as e:
        log.info(f"[{cid}] WS 结束: {e}")
    finally:
        for key in list(_agent_cache.keys()):
            if session_id and session_id in key:
                del _agent_cache[key]

async def health(request):
    return JSONResponse({"status": "ok", "service": "hermes-bridge", "v": "0.7.0"})

async def memory_list(request):
    mem = HERMES_HOME / "memories"
    files = [{"name": f.name, "size": f.stat().st_size}
             for f in sorted(mem.glob("*.md"))] if mem.exists() else []
    return JSONResponse({"files": files})

async def memory_read(request):
    file = request.query_params.get("file", "MEMORY.md")
    path = HERMES_HOME / "memories" / file
    content, err = read_file(str(path))
    if err: return JSONResponse({"error": err}, status_code=404)
    return JSONResponse({"file": file, "content": content})

async def memory_write(request):
    try:
        body = await request.json()
        file = body.get("file", "MEMORY.md")
        err = write_file(str(HERMES_HOME / "memories" / file), body.get("content", ""))
        if err: return JSONResponse({"error": err}, status_code=500)
        return JSONResponse({"ok": True, "file": file})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

# ============ 会话存储 API ============

def _session_file(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"

def _list_sessions() -> list:
    sessions = []
    for f in SESSIONS_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sessions.append({
                "id": data.get("id", f.stem),
                "title": data.get("title", "未命名"),
                "created_at": data.get("created_at", 0),
                "updated_at": data.get("updated_at", 0),
                "message_count": len(data.get("messages", [])),
                "model": data.get("model", ""),
            })
        except:
            pass
    return sorted(sessions, key=lambda x: x["updated_at"], reverse=True)

async def sessions_list(request):
    return JSONResponse({"sessions": _list_sessions()})

async def sessions_read(request):
    sid = request.path_params.get("id")
    if not sid:
        return JSONResponse({"error": "缺少 session id"}, status_code=400)
    f = _session_file(sid)
    if not f.exists():
        return JSONResponse({"error": "会话不存在"}, status_code=404)
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
        return JSONResponse({"session": data})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

async def sessions_save(request):
    try:
        body = await request.json()
        sid = body.get("id")
        if not sid:
            return JSONResponse({"error": "缺少 session id"}, status_code=400)
        f = _session_file(sid)
        # 合并消息
        existing = {}
        if f.exists():
            try: existing = json.loads(f.read_text(encoding="utf-8"))
            except: pass
        existing.update(body)
        existing["updated_at"] = int(Path(__file__).stat().st_mtime)
        f.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

async def sessions_delete(request):
    sid = request.path_params.get("id")
    if not sid:
        return JSONResponse({"error": "缺少 session id"}, status_code=400)
    f = _session_file(sid)
    if f.exists():
        f.unlink()
    return JSONResponse({"ok": True})

async def config_read(request):
    cfg_path = HERMES_HOME / "config.yaml"
    content, err = read_file(str(cfg_path))
    if err: return JSONResponse({"error": err}, status_code=404)
    return JSONResponse({"content": content})

async def config_write(request):
    try:
        body = await request.json()
        err = write_file(str(HERMES_HOME / "config.yaml"), body.get("content", ""))
        if err: return JSONResponse({"error": err}, status_code=500)
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)

app = Starlette(
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]),
    ],
    routes=[
        Route("/health", health),
        Route("/memory/list", memory_list),
        Route("/memory/read", memory_read),
        Route("/memory/write", memory_write, methods=["PUT"]),
        Route("/api/sessions", sessions_list),
        Route("/api/sessions/{id}", sessions_read),
        Route("/api/sessions/{id}", sessions_save, methods=["PUT"]),
        Route("/api/sessions/{id}", sessions_delete, methods=["DELETE"]),
        Route("/config/read", config_read),
        Route("/config/write", config_write, methods=["PUT"]),
        WebSocketRoute("/ws/chat", ws_chat_endpoint),
    ],
)

if __name__ == "__main__":
    port = int(os.environ.get("HERMES_BRIDGE_PORT", "9120"))
    log.info(f"═══════════════════════════════════════")
    log.info(f"  Hermes Bridge Server v0.7.0")
    log.info(f"  HTTP: http://localhost:{port}/")
    log.info(f"  WS:   ws://localhost:{port}/ws/chat")
    log.info(f"═══════════════════════════════════════")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info", access_log=False)
