from my_agent.modules.base import BaseSearchModule


class HealthModule(BaseSearchModule):
    topic = "health"
    header = "Theo cam nang y te va suc khoe (mang tinh tham khao, khong thay the chan doan bac si):"
    empty_message = "Khong tim thay thong tin y te chuyen nganh nao lien quan den cau hoi."

    def search_health_info(self, query: str) -> str:
        return self.search(query)

    def format_results(self, results: list[dict]) -> str:
        lines = [self.header, ""]
        for result in results:
            text = result.get("text", "").replace("\n", " ")
            lines.append(f"- {text}")
        return "\n".join(lines)
