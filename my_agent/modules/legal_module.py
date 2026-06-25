from my_agent.modules.base import BaseSearchModule


class LegalModule(BaseSearchModule):
    topic = "legal"
    header = "--- DU LIEU PHAP LY ---"
    empty_message = "Du lieu noi bo khong co thong tin phap ly nay. Vui long kiem tra tren web."

    def search_legal_knowledge(self, query: str) -> str:
        return self.search(query)
