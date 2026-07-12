"""对话历史存储模块：Redis"""

import json
from datetime import datetime
import redis
from config import HISTORY_TURNS, REDIS_HOST, REDIS_PORT

# Redis 连接（支持环境变量配置）
_r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

# Redis key 前缀
_KEY_PREFIX = "rag:session:"
# 会话列表 key（记录所有 session_id）
_SESSION_LIST_KEY = "rag:sessions"
# 每条消息的 TTL（30 天自动过期）
_TTL = 30 * 24 * 3600


def init_db():
    """Redis 不需要建表，此函数保持兼容"""
    pass


def save_message(session_id: str, role: str, content: str):
    """保存一条对话消息到 Redis List"""
    key = f"{_KEY_PREFIX}{session_id}"
    msg = json.dumps({
        "role": role,
        "content": content,
        "created_at": datetime.now().isoformat(),
    }, ensure_ascii=False)
    _r.rpush(key, msg)
    _r.expire(key, _TTL)
    # 记录 session_id 到集合
    _r.sadd(_SESSION_LIST_KEY, session_id)
    _r.expire(_SESSION_LIST_KEY, _TTL)


def get_history(session_id: str, turns: int = HISTORY_TURNS) -> list[dict]:
    """获取最近 N 轮对话历史（每轮 = user + assistant = 2 条消息）"""
    key = f"{_KEY_PREFIX}{session_id}"
    # 取最后 N*2 条消息
    messages = _r.lrange(key, -turns * 2, -1)
    return [json.loads(m) for m in messages]


def clear_session(session_id: str):
    """清除指定会话"""
    key = f"{_KEY_PREFIX}{session_id}"
    _r.delete(key)
    _r.srem(_SESSION_LIST_KEY, session_id)


def list_sessions(limit: int = 10) -> list[dict]:
    """列出最近的会话及其最后一条消息时间"""
    session_ids = _r.smembers(_SESSION_LIST_KEY)
    results = []
    for sid in session_ids:
        key = f"{_KEY_PREFIX}{sid}"
        last_msg = _r.lindex(key, -1)
        last_time = ""
        if last_msg:
            try:
                last_time = json.loads(last_msg).get("created_at", "")[:19]
            except json.JSONDecodeError:
                pass
        results.append({"session_id": sid, "last_message_at": last_time})
    # 按时间倒序
    results.sort(key=lambda x: x["last_message_at"], reverse=True)
    return results[:limit]
