"""
Guardrail Layer — Chống hallucination cho tool_agent.

Sử dụng ADK callbacks để enforce tool calling ở code layer:
- before_agent_callback: Reset trạng thái mỗi lượt chat mới.
- after_tool_callback: Đánh dấu đã gọi tool thành công.
- after_model_callback: GUARDRAIL — Nếu LLM trả text mà chưa gọi tool
  → reject response → thay bằng synthetic function_call tự động.

Lưu ý: KHÔNG ảnh hưởng tới lịch sử hội thoại (ADK Session quản lý riêng).
Chỉ reset 1 biến cờ _tool_called mỗi lượt.
"""

import re
import uuid
import time
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from my_agent.core.cache_manager import CacheManager

cache_manager = CacheManager()



# ============================================================
# Danh sách câu hỏi MIỄN KIỂM TRA (không cần gọi tool)
# ============================================================

EXEMPT_PATTERNS = [
    # Date / Time
    r"mấy giờ", r"ngày mấy", r"hôm nay", r"ngày mai", r"hôm qua",
    r"thứ mấy", r"bây giờ", r"năm nay", r"tháng này",
    # Greetings (phòng vệ, thực tế không nên đến tool_agent)
    r"cảm ơn", r"cám ơn", r"thank", r"chào",
    r"^ok$", r"^okie$", r"^ừ$", r"^uh$",
    r"được rồi", r"hiểu rồi", r"bye",
]

_EXEMPT_RE = re.compile(
    "|".join(EXEMPT_PATTERNS),
    re.IGNORECASE | re.UNICODE,
)


def _is_exempt_query(query: str) -> bool:
    """Kiểm tra câu hỏi có nằm trong danh sách miễn kiểm tra không."""
    if not query or len(query.strip()) < 2:
        return True  # Câu quá ngắn → không cần search
    return bool(_EXEMPT_RE.search(query.strip()))


def _has_function_call(llm_response: LlmResponse) -> bool:
    """Kiểm tra response có chứa function_call không."""
    if not llm_response or not llm_response.content:
        return False
    if not llm_response.content.parts:
        return False
    return any(
        hasattr(p, "function_call") and p.function_call
        for p in llm_response.content.parts
    )


def _extract_user_query(callback_context) -> str:
    """Trích xuất câu hỏi gần nhất của user từ context."""
    # Ưu tiên user_content (tin nhắn hiện tại)
    if callback_context.user_content and callback_context.user_content.parts:
        for part in callback_context.user_content.parts:
            if hasattr(part, "text") and part.text:
                return part.text.strip()
    return ""


def _build_forced_search(query: str) -> LlmResponse:
    """Tạo LlmResponse giả chứa function_call tới web_search."""
    call_id = f"adk_tool_call_{uuid.uuid4().hex}"
    fc = types.FunctionCall(name="web_search", args={"query": query}, id=call_id)
    part = types.Part(function_call=fc)
    content = types.Content(role="model", parts=[part])
    return LlmResponse(content=content)


# ============================================================
# ADK Callbacks (5 callbacks — đăng ký vào tool_agent)
#
# Thứ tự thực thi thực tế theo thời gian:
#   1. before_agent  → Reset trạng thái đầu mỗi lượt chat
#   2. after_model   → Kiểm tra kết quả LLM sinh ra (Guardrail chính)
#   3. before_tool   → Rate limit + Cache hit check trước khi tool chạy
#   4. after_tool    → Ghi latency + lưu cache sau khi tool chạy xong
#   5. after_agent   → In Trace Log tổng kết sau khi agent hoàn tất
# ============================================================

def tool_agent_before_agent(callback_context):
    """
    Chạy ĐẦU mỗi lượt chat → Reset cờ guardrail.
    KHÔNG ảnh hưởng lịch sử hội thoại (Session).
    """
    callback_context.state["_tool_called"] = False
    callback_context.state["_force_retry_count"] = 0
    return None  # Không thay đổi flow


def tool_agent_before_tool(tool, args, tool_context):
    """
    Kích hoạt TRƯỚC KHI tool chạy.
    Nhiệm vụ:
    - Kiểm tra giới hạn số lần gọi tool mỗi request (tránh lặp vô hạn).
    - Lưu thời điểm bắt đầu gọi tool để đo độ trễ thực thi.
    - Kiểm tra cache tìm kiếm web để tối ưu hóa hiệu năng (cache hit).
    """
    tool_name = getattr(tool, "name", str(tool))
    
    # 1. Khởi tạo & kiểm tra giới hạn (Max 5 lần/request)
    if "_tool_call_count" not in tool_context.state:
        tool_context.state["_tool_call_count"] = 0
    tool_context.state["_tool_call_count"] += 1
    
    if tool_context.state["_tool_call_count"] > 5:
        print(f"[MONITOR] ⚠️ Chặn gọi tool '{tool_name}' do vượt quá giới hạn 5 lần/request.")
        return {
            "status": "failed",
            "tool": tool_name,
            "reason": "Vượt quá giới hạn số lần gọi công cụ trong một lượt chat."
        }
        
    # 2. Ghi nhận thời gian bắt đầu
    tool_context.state[f"_start_time_{tool_name}"] = time.time()
    
    # 3. Cache hit check cho web_search và web_deep_search (cache 1 giờ cho web)
    if tool_name in ["web_search", "web_deep_search"] and "query" in args:
        query = args["query"]
        cached_res = cache_manager.get(query, topic=f"web:{tool_name}", ttl_hours=1)
        if cached_res:
            print(f"[MONITOR] ⚡ [CACHE HIT] Sử dụng kết quả tìm kiếm web đã lưu cho: '{query}'")
            return cached_res
            
    return None


def tool_agent_after_tool(tool, args, tool_context, tool_response):
    """
    Chạy SAU khi tool thực thi xong.
    Nhiệm vụ: Ghi nhận độ trễ và lưu kết quả tìm kiếm web thành công vào cache.
    """
    tool_context.state["_tool_called"] = True
    tool_name = getattr(tool, "name", str(tool))
    
    # 1. Tính toán độ trễ thực thi
    start_time = tool_context.state.get(f"_start_time_{tool_name}")
    if start_time:
        latency = time.time() - start_time
        if "_tool_latencies" not in tool_context.state:
            tool_context.state["_tool_latencies"] = {}
        tool_context.state["_tool_latencies"][tool_name] = tool_context.state["_tool_latencies"].get(tool_name, 0.0) + latency
        print(f"[MONITOR] Tool '{tool_name}' thực thi xong trong {latency:.2f}s ✓")
        
    # 2. Lưu kết quả tìm kiếm web mới vào cache nếu thành công
    if tool_name in ["web_search", "web_deep_search"] and "query" in args:
        res_str = None
        if isinstance(tool_response, str):
            res_str = tool_response
        elif isinstance(tool_response, dict) and "result" in tool_response:
            res_str = tool_response["result"]
            
        if res_str and isinstance(res_str, str) and "failed" not in res_str:
            cache_manager.set(args["query"], topic=f"web:{tool_name}", content=res_str)
            
    print(f"[GUARDRAIL] Tool '{tool_name}' đã được gọi ✓")
    return tool_response


def tool_agent_after_model(callback_context, llm_response):
    """
    GUARDRAIL CHÍNH — Chạy SAU mỗi lần LLM trả response.

    Logic:
    1. Đã gọi tool rồi? → Cho qua (final answer).
    2. Response có function_call? → Cho qua (đang gọi tool).
    3. Câu hỏi exempt (ngày/giờ/chào)? → Cho qua.
    4. Đã retry 1 lần? → Cho qua (tránh loop vô hạn).
    5. Còn lại: REJECT → Thay bằng web_search tự động.
    """
    # 1. Đã gọi tool → đây là final answer → cho qua
    if callback_context.state.get("_tool_called", False):
        return None

    # 2. Response đã chứa function_call → model đang gọi tool → cho qua
    if _has_function_call(llm_response):
        return None

    # 3. Trích xuất câu hỏi user
    user_query = _extract_user_query(callback_context)

    # 4. Câu hỏi exempt → cho qua
    if _is_exempt_query(user_query):
        print(f"[GUARDRAIL] Exempt query, cho qua: '{user_query[:50]}'")
        return None

    # 5. Giới hạn retry (tránh loop vô hạn)
    retry_count = callback_context.state.get("_force_retry_count", 0)
    if retry_count >= 1:
        print(f"[GUARDRAIL] Đã retry {retry_count} lần, cho qua để tránh loop.")
        return None

    # === REJECT & FORCE TOOL CALL ===
    callback_context.state["_force_retry_count"] = retry_count + 1
    print(
        f"[GUARDRAIL] ⚠️ CHẶN response text-only! "
        f"Force web_search cho: '{user_query[:80]}'"
    )
    return _build_forced_search(user_query)


def tool_agent_after_agent(callback_context):
    """
    Kích hoạt KHI AGENT KẾT THÚC lượt chạy.
    Nhiệm vụ: Tổng hợp hiệu năng và in ra Trace Log phục vụ giám sát/debug.
    """
    print(f"\n==================== [TRACE LOG - TOOL_AGENT] ====================")
    
    # 1. Tổng lượt gọi tool
    call_count = callback_context.state.get("_tool_call_count", 0)
    print(f"🔹 Tổng số lần gọi Tool: {call_count}")
    
    # 2. Độ trễ của từng tool
    latencies = callback_context.state.get("_tool_latencies", {})
    if latencies:
        print("🔹 Chi tiết độ trễ thực thi:")
        total_tool_latency = 0.0
        for t_name, dur in latencies.items():
            print(f"   ├── {t_name}: {dur:.2f}s")
            total_tool_latency += dur
        print(f"   └── Tổng thời gian chạy Tool: {total_tool_latency:.2f}s")
    else:
        print("🔹 Không sử dụng công cụ nào trong lượt chạy này.")
        
    # 3. Giám sát Guardrail
    force_count = callback_context.state.get("_force_retry_count", 0)
    if force_count > 0:
        print(f"🔹 Guardrail Warning: ⚠️ Đã ép gọi Tool tự động {force_count} lần do Model ảo giác.")
        
    print("=================================================================\n")
    return None
