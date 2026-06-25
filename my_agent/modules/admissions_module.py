from my_agent.modules.base import BaseSearchModule


class AdmissionsModule(BaseSearchModule):
    topic = "admissions"
    header = "--- QUY CHE TUYEN SINH ---"
    empty_message = "Du lieu noi bo khong co thong tin tuyen sinh nay. Vui long kiem tra tren web."

    def search_admissions_info(self, query: str) -> str:
        return self.search(query)
