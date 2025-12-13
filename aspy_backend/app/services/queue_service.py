# app/services/queue_service.py - CREATE THIS FILE
import json
import os
from typing import Optional, Dict, Any
import logging

# Lazy import for redis to avoid syntax errors
redis = None
try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)


class QueueService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_queue()
        return cls._instance

    def _init_queue(self):
        """Initialize Redis connection or use in-memory queue"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            self.redis = redis.Redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=1)
            self.redis.ping()
            logger.info("✅ Redis connected successfully")
            self.use_redis = True
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory queue: {e}")
            self.redis = None
            self.memory_queue = []
            self.use_redis = False

    def enqueue(self, queue_name: str, job_data: Dict[str, Any]) -> bool:
        """Add job to queue"""
        try:
            if self.use_redis and self.redis:
                self.redis.lpush(queue_name, json.dumps(job_data))
                logger.debug(f"Job enqueued to Redis {queue_name}: {job_data.get('job_id')}")
            else:
                self.memory_queue.append(job_data)
                logger.debug(f"Job added to memory queue: {job_data.get('job_id')}")
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            return False

    def dequeue(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get next job from queue"""
        try:
            if self.use_redis and self.redis:
                job_data = self.redis.rpop(queue_name)
                if job_data:
                    return json.loads(job_data)
            elif self.memory_queue:
                return self.memory_queue.pop(0) if self.memory_queue else None
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue job: {e}")
            return None

    def get_queue_length(self, queue_name: str) -> int:
        """Get queue length"""
        try:
            if self.use_redis and self.redis:
                return self.redis.llen(queue_name)
            else:
                return len(self.memory_queue)
        except Exception as e:
            logger.error(f"Failed to get queue length: {e}")
            return 0


# Global instance
queue_service = QueueService()