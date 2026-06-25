import os
import json
import hashlib
import time
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            # Mac dinh luu vao my_agent/data/cache
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            cache_dir = os.path.join(base_dir, "data", "cache")
        
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_hash(self, text: str) -> str:
        """Tao ma hash duy nhat cho cau truy van."""
        return hashlib.md5(text.strip().lower().encode("utf-8")).hexdigest()

    def get(self, query: str, topic: str, ttl_hours: int = 24) -> str | None:
        """Lay du lieu tu cache neu con han (TTL)."""
        cache_key = self._get_hash(f"{topic}:{query}")
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Kiem tra thoi han
            cached_time = datetime.fromisoformat(data["timestamp"])
            if datetime.now() > cached_time + timedelta(hours=ttl_hours):
                return None # Cache da het han
            
            return data["content"]
        except Exception:
            return None

    def set(self, query: str, topic: str, content: str):
        """Luu du lieu vao cache."""
        cache_key = self._get_hash(f"{topic}:{query}")
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")

        data = {
            "query": query,
            "topic": topic,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Loi khi ghi cache: {e}")
