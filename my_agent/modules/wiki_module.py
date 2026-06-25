from my_agent.modules.base import BaseSearchModule


class WikiModule(BaseSearchModule):
    topic = "wiki"
    header = "--- TRI THUC BACH KHOA ---"
    empty_message = "Khong tim thay thong tin phu hop trong kho tri thuc bach khoa noi bo."

    def search_general_knowledge(self, query: str) -> str:
        return self.search(query)
