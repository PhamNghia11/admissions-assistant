from abc import ABC

from my_agent.core.rag_engine import RAGManager


class BaseModule(ABC):
    def __init__(self, engine: RAGManager | None = None) -> None:
        self.engine = engine or RAGManager()


class BaseSearchModule(BaseModule):
    topic = ""
    header = ""
    empty_message = "Khong tim thay du lieu phu hop."
    result_limit = 5

    def search(self, query: str, limit: int | None = None) -> str:
        limit = limit or self.result_limit
        results = self.engine.search(self.topic, query, limit=limit)
        if not results:
            return self.empty_message
        return self.format_results(results)

    def format_results(self, results: list[dict]) -> str:
        sections = [self.header, ""]
        for index, result in enumerate(results, start=1):
            text = result.get("text", "Noi dung trong")
            sections.append(f"({index}) {text}")
            sections.append("")
        return "\n".join(sections).strip()
