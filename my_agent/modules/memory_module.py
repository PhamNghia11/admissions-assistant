from datetime import datetime


from my_agent.modules.base import BaseModule


class MemoryModule(BaseModule):
    """
    Long-term memory backed by the same vector infrastructure as the RAG system.
    """

    def __init__(self, engine=None):
        super().__init__(engine=engine)
        self.topic = "memory"
        self.db = self.engine.get_db_connection(self.topic)
        self.table_name = f"{self.topic}_data"

    def ghi_nho(self, thong_tin: str, category: str = "general") -> str:
        """Ghi nho thong tin vao bo nho voi phan loai (profile, preference, fact, general)."""
        vectors = self.engine.embed_text([thong_tin])
        data = [
            {
                "vector": vectors[0].tolist(),
                "text": thong_tin,
                "category": category,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        ]

        if self.table_name in self.db.table_names():
            self.db.open_table(self.table_name).add(data)
        else:
            self.db.create_table(self.table_name, data=data)

        return f"Da ghi nho thong tin vao muc [{category}] thanh cong."

    def nho_lai(self, truy_van: str, category_filter: str = None) -> str:
        """Truy xuat tri nho, co the loc theo category."""
        if self.table_name not in self.db.table_names():
            return "Tri nho hien dang trong rong."

        table = self.db.open_table(self.table_name)
        
        # Thuc hien tim kiem vector
        query_vec = self.engine.embed_text([truy_van])[0]
        search_query = table.search(query_vec)
        
        # Neu co loc theo category (vi du: profile)
        if category_filter:
            safe_category = category_filter.replace("'", "").replace('"', '').strip()
            search_query = search_query.where(f"category = '{safe_category}'")
            
        results = search_query.limit(5).to_list()
        
        if not results:
            return "Khong co manh ky uc nao phu hop."

        lines = ["--- TRI NHO DUOC KICH HOAT ---", ""]
        for result in results:
            text = result.get("text", "")
            cat = result.get("category", "general")
            timestamp = result.get("timestamp", "")
            lines.append(f"[{cat} | {timestamp}]: {text}")
        return "\n".join(lines)
