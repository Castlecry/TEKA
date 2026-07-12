"""Redis 缓存增强模块：热门问题、统计缓存、搜索缓存、速率限制"""

import json
import hashlib
from datetime import datetime, timedelta
import redis
from config import REDIS_HOST, REDIS_PORT

_r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=1, decode_responses=True)

# ========== 热门问题排行（Sorted Set）==========

_HOT_QUESTIONS_KEY = "stats:hot_questions"
_SEARCH_CACHE_PREFIX = "cache:search:"
_STATS_CACHE_KEY = "cache:dashboard_stats"
_RATE_LIMIT_PREFIX = "rate_limit:"
_CACHE_TTL = 300  # 5 分钟
_SEARCH_CACHE_TTL = 600  # 10 分钟


def track_question(query: str):
    """记录用户提问，更新热门问题排行"""
    if not query or len(query) < 2:
        return
    # 归一化：截断长问题，去重
    normalized = query.strip()[:100]
    _r.zincrby(_HOT_QUESTIONS_KEY, 1, normalized)


def get_hot_questions(limit: int = 10) -> list[dict]:
    """获取热门问题 Top-N"""
    items = _r.zrevrange(_HOT_QUESTIONS_KEY, 0, limit - 1, withscores=True)
    return [{"question": q, "count": int(score)} for q, score in items]


# ========== 搜索/检索结果缓存 ==========

def _cache_key(query: str) -> str:
    return f"{_SEARCH_CACHE_PREFIX}{hashlib.md5(query.encode()).hexdigest()}"


def get_search_cache(query: str) -> list[dict] | None:
    """尝试从缓存获取搜索结果"""
    key = _cache_key(query)
    data = _r.get(key)
    if data:
        return json.loads(data)
    return None


def set_search_cache(query: str, results: list[dict], ttl: int = _SEARCH_CACHE_TTL):
    """缓存搜索结果"""
    key = _cache_key(query)
    _r.setex(key, ttl, json.dumps(results, ensure_ascii=False))


# ========== Dashboard 统计缓存 ==========

def get_dashboard_stats() -> dict | None:
    """获取缓存的仪表盘统计数据"""
    data = _r.get(_STATS_CACHE_KEY)
    if data:
        return json.loads(data)
    return None


def set_dashboard_stats(stats: dict, ttl: int = _CACHE_TTL):
    """缓存仪表盘统计数据"""
    _r.setex(_STATS_CACHE_KEY, ttl, json.dumps(stats))


def invalidate_stats():
    """使统计缓存失效"""
    _r.delete(_STATS_CACHE_KEY)


# ========== 速率限制 ==========

def check_rate_limit(user_id: int, endpoint: str = "chat",
                     max_requests: int = 30, window_seconds: int = 60) -> tuple[bool, int]:
    """检查用户速率限制，返回 (是否允许, 剩余次数)"""
    key = f"{_RATE_LIMIT_PREFIX}{endpoint}:{user_id}"
    now = datetime.now().timestamp()

    # 移除窗口外的记录
    _r.zremrangebyscore(key, 0, now - window_seconds)

    # 统计当前窗口内请求数
    count = _r.zcard(key)
    remaining = max_requests - count

    if remaining <= 0:
        return False, 0

    # 记录本次请求
    _r.zadd(key, {str(now): now})
    _r.expire(key, window_seconds * 2)

    return True, remaining - 1
