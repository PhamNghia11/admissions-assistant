import os
import io
from pathlib import Path
from pypdf import PdfReader
from docx import Document
from google.adk.tools.tool_context import ToolContext
from my_agent.core.environment import EnvironmentConfig
from my_agent.core.rag_engine import RAGManager
from my_agent.modules.admissions_module import AdmissionsModule
from my_agent.modules.health_module import HealthModule
from my_agent.modules.legal_module import LegalModule
from my_agent.modules.memory_module import MemoryModule
from my_agent.modules.wiki_module import WikiModule
from my_agent.services.web_service import WebContentService


class AssistantApplication:

    def __init__(self, config: EnvironmentConfig | None = None) -> None:
        self.config = config or EnvironmentConfig.load()
        self.engine = RAGManager(model_name=self.config.embedding_model)
        self.web_service = WebContentService()
        self.modules = self._build_modules()

    def _build_modules(self) -> dict[str, object]:
        return {
            "legal": LegalModule(engine=self.engine),
            "wiki": WikiModule(engine=self.engine),
            "admissions": AdmissionsModule(engine=self.engine),
            "health": HealthModule(engine=self.engine),
            "memory": MemoryModule(engine=self.engine),
        }

    # ============================================================
    # RAG Tools
    # ============================================================

    def search_legal(self, query: str) -> str:
        """Tra cuu cac van ban phap luat, nghi dinh, thong tu lien quan den cau hoi."""
        return self.modules["legal"].search_legal_knowledge(query)

    def search_wiki(self, query: str) -> str:
        """Tra cuu cac kien thuc tong hop, lich su, khoa hoc, van hoa tu Wikipedia."""
        return self.modules["wiki"].search_general_knowledge(query)

    def search_admissions(self, query: str) -> str:
        """Tra cuu cac thong tin ve tuyen sinh, ma nganh, hoc phi va thu tuc nhap hoc."""
        return self.modules["admissions"].search_admissions_info(query)

    def search_health(self, query: str) -> str:
        """Tra cuu cac thong tin ve suc khoe, y te, benh hoc, thuoc va loi khuyen y khoa."""
        return self.modules["health"].search_health_info(query)

    # ============================================================
    # Web Tools
    # ============================================================

    def web_search(self, query: str) -> str:
        """Tim kiem nhanh internet cho cac thong tin thoi su. Chi lay cac doan trich ngan."""
        return self.web_service.search_web(query, deep=False)

    def web_deep_search(self, query: str) -> str:
        """Tim kiem sau internet. AI se tu dong doc noi dung chi tiet cua nhieu trang web de tong hop. 
        Dung cho cac cau hoi kho, can du lieu chi tiet va chinh xac nhat."""
        return self.web_service.search_web(query, deep=True)

    def browse_url(self, url: str) -> str:
        """Tu dong truy cap va doc toan bo noi dung van ban trong mot duong link website URL."""
        return self.web_service.read_url(url)

    # ============================================================
    # Memory Tools
    # ============================================================

    def save_memory(self, thong_tin: str, category: str = "general") -> str:
        """Luu tru thong tin, so thich, hoac su kien vao bo nho dai han. 
        Category co the la: 'profile' (ca nhan), 'preference' (so thich), 'fact' (su kien), 'general' (chung)."""
        return self.modules["memory"].ghi_nho(thong_tin, category=category)

    def recall_memory(self, truy_van: str, category: str = None) -> str:
        """Truy xuat tri nho dai han. Co the loc theo category ('profile', 'preference', 'reflection', etc.) neu can thiet."""
        return self.modules["memory"].nho_lai(truy_van, category_filter=category)

    # ============================================================
    # Vision Tool
    # ============================================================

    async def parse_document(self, file_name: str, tool_context: ToolContext) -> str:
        """Doc noi dung tu tep tin duoc tai len (PDF, Word, TXT, CSV, Markdown).

        Args:
            file_name: Ten tep tin chinh xac da duoc tai len trong phien lam viec nay.
        """
        # 1. Load bytes tu ADK artifact store
        part = await tool_context.load_artifact(file_name)
        if part is None:
            return f"Loi: Khong tim thay tep '{file_name}'. Hay dam bao tep da duoc tai len dung ten."

        # 2. Lay bytes va mime_type
        if part.inline_data is None or part.inline_data.data is None:
            return f"Loi: Du lieu tep '{file_name}' rong hoac khong hop le."

        data: bytes = part.inline_data.data
        mime_type: str = part.inline_data.mime_type or ""
        ext = os.path.splitext(file_name)[1].lower()

        # 3. Trich xuat text theo dinh dang
        try:
            if ext == ".pdf" or "pdf" in mime_type:
                reader = PdfReader(io.BytesIO(data))
                text = ""
                for page in reader.pages:
                    text += (page.extract_text() or "") + "\n"
                return text
            elif ext == ".docx" or "wordprocessingml" in mime_type:
                doc = Document(io.BytesIO(data))
                return "\n".join([para.text for para in doc.paragraphs])
            elif ext in [".txt", ".md", ".csv", ".tsv"] or mime_type.startswith("text/"):
                return data.decode("utf-8", errors="ignore")
            else:
                return f"Loi: Dinh dang tep '{ext}' chua duoc ho tro. Hien ho tro: PDF, DOCX, TXT, CSV."
        except Exception as e:
            return f"Loi khi doc tep '{file_name}': {str(e)}"
