import redis
import json
import base64
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

class TemporaryScanCache:
    def __init__(self):
        try:
            self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
            self.r.ping()
            self.redis_available = True
        except Exception:
            self.redis_available = False
            self.memory_store = {}

    def save_session(self, session_id: str, pages_data: list, ttl_seconds: int = 86400):
        data_str = json.dumps(pages_data)
        if self.redis_available:
            self.r.setex(f"scan_session:{session_id}", ttl_seconds, data_str)
        else:
            self.memory_store[f"scan_session:{session_id}"] = data_str

    def get_session(self, session_id: str) -> list:
        if self.redis_available:
            data_str = self.r.get(f"scan_session:{session_id}")
        else:
            data_str = self.memory_store.get(f"scan_session:{session_id}")

        if data_str:
            return json.loads(data_str)
        return []

    def delete_session(self, session_id: str):
        if self.redis_available:
            self.r.delete(f"scan_session:{session_id}")
        else:
            self.memory_store.pop(f"scan_session:{session_id}", None)

scan_cache = TemporaryScanCache()
