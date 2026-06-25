import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from my_agent.core.cache_manager import CacheManager


class WebContentService:
    def __init__(self):
        self.cache = CacheManager()

    def read_url(self, url: str) -> str:
        response = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "table", "button"]):
            tag.extract()
        text = soup.get_text(separator=" ", strip=True)
        # Loc bo cac khoang trang thua
        text = " ".join(text.split())
        return text[:4000]

    def _safe_read_url(self, url: str) -> str | None:
        """Doc URL an toan - tra ve None neu loi (403, timeout, etc.) thay vi crash."""
        try:
            return self.read_url(url)
        except Exception as e:
            print(f"  ! Khong doc duoc {url}: {type(e).__name__}: {e}")
            return None

    def search_web(self, query: str, deep: bool = False) -> str:
        """Tim kiem web. Neu deep=True, AI se tu dong doc noi dung chi tiet cua 3 ket qua dau tien."""
        # 1. Kiem tra cache truoc
        topic = "web_deep" if deep else "web_quick"
        cached_result = self.cache.get(query, topic, ttl_hours=24)
        if cached_result:
            print(f"--- [CACHE HIT] Su dung ket qua cu cho: {query} ---")
            return cached_result

        results = list(DDGS().text(query, max_results=10))

        if not results:
            return "Khong tim thay ket qua phu hop tren web."

        final_result = ""
        if not deep:
            snippets = []
            for item in results:
                snippets.append(f"- {item.get('title')}\n  {item.get('body')}\n  {item.get('href')}")
            final_result = "KET QUA TIM KIEM (NHANH):\n" + "\n\n".join(snippets)
        else:
            # Deep Search: Doc noi dung chi tiet cua top 3 ket qua
            print(f"--- Dang thuc hien Deep Search cho: {query} ---")
            deep_content = ["--- KET QUA DEEP SEARCH (DA DOC CHI TIET) ---", ""]
            success_count = 0
            for i, item in enumerate(results[:6]):  # Thu 6 URL, lay 3 thanh cong
                if success_count >= 3:
                    break
                url = item.get("href")
                title = item.get("title")
                print(f"  > Dang doc trang {i+1}: {url}")
                content = self._safe_read_url(url)
                if content is None:
                    continue  # Bo qua URL loi, thu URL tiep theo
                short_content = content[:2000] if len(content) > 2000 else content
                deep_content.append(f"NGUON {success_count+1}: {title}\nURL: {url}\nNOI DUNG: {short_content}\n---")
                success_count += 1

            if success_count == 0:
                # Neu KHONG doc duoc trang nao, tra ve snippets thay vi crash
                snippets = []
                for item in results[:5]:
                    snippets.append(f"- {item.get('title')}\n  {item.get('body')}\n  {item.get('href')}")
                final_result = "KET QUA TIM KIEM (KHONG DOC DUOC CHI TIET):\n" + "\n\n".join(snippets)
            else:
                final_result = "\n\n".join(deep_content)
        
        # Thêm block nguồn trích dẫn rõ ràng để LLM luôn cite
        sources_block = "\n\n--- NGUON TRICH DAN (BAT BUOC TRICH DAN IT NHAT 1 NGUON) ---\n"
        for i, item in enumerate(results[:3]):
            sources_block += f"[{i+1}] {item.get('title', '')} - {item.get('href', '')}\n"
        final_result += sources_block

        # 2. Luu vao cache cho lan sau
        self.cache.set(query, topic, final_result)
        return final_result
