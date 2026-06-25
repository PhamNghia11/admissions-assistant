"""
Retry Manager - Co che retry tu dong cho cac Tool Functions.

Su dung ADK Callback (on_tool_error_callback) de retry o tang framework,
thay vi decorator boc ngoai ham.

Workflow:
    Agent goi Tool -> Tool Function -> Success? -> Return Result
                                    -> NO (Exception) -> on_tool_error_callback
                                        -> retryable? -> YES -> Backoff Delay -> Re-invoke func
                                                      -> NO  -> Return Structured Error Dict
"""

import time

import requests
import httpx
from ddgs.exceptions import DDGSException, RatelimitException, TimeoutException as DDGSTimeoutException


# ============================================================
# Cau hinh retry
# ============================================================

# Cac exception co the retry (loi mang, timeout)
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    # requests.exceptions.HTTPError KHONG retry (403/404 la loi vinh vien)
    DDGSException,
    RatelimitException,
    DDGSTimeoutException,
    httpx.ConnectError,
    httpx.TimeoutException,
)

# Cau hinh retry theo nhom tool
RETRY_CONFIG = {
    # Web tools: retry 3 lan, delay bat dau 1s
    "web_search": {"max_retries": 3, "base_delay": 1.0},
    "web_deep_search": {"max_retries": 3, "base_delay": 1.0},
    "browse_url": {"max_retries": 3, "base_delay": 1.0},
    # RAG tools: retry 2 lan, delay bat dau 0.5s
    "search_legal": {"max_retries": 2, "base_delay": 0.5},
    "search_wiki": {"max_retries": 2, "base_delay": 0.5},
    "search_admissions": {"max_retries": 2, "base_delay": 0.5},
    "search_health": {"max_retries": 2, "base_delay": 0.5},
    # Memory tools: retry 2 lan, delay bat dau 0.5s
    "save_memory": {"max_retries": 2, "base_delay": 0.5},
    "recall_memory": {"max_retries": 2, "base_delay": 0.5},
}

# Cau hinh mac dinh cho tool khong co trong danh sach
DEFAULT_RETRY = {"max_retries": 2, "base_delay": 1.0}
BACKOFF_FACTOR = 2.0


def classify_error(exc: Exception) -> str:
    """Phan loai exception thanh error_type co cau truc."""
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return "NETWORK_ERROR"
    if isinstance(exc, OSError):
        return "DB_ERROR"
    if isinstance(exc, FileNotFoundError):
        return "PARSE_ERROR"
    if isinstance(exc, (ValueError, TypeError)):
        return "VALIDATION_ERROR"
    if isinstance(exc, (DDGSException,)):
        return "SEARCH_ENGINE_ERROR"
    return "API_ERROR"


def _build_error_dict(tool_name: str, exc: Exception, attempts: int, max_retries: int) -> dict:
    """Tao Structured Error Response dang dict (ADK callback format)."""
    error_type = classify_error(exc)
    
    # Goi y cho AI cach xin loi/huong dan nguoi dung
    suggestions = {
        "NETWORK_ERROR": "Vui lòng kiểm tra lại kết nối internet hoặc thử lại sau vài giây.",
        "DB_ERROR": "Cơ sở dữ liệu tri thức đang bảo trì, vui lòng thử lại sau.",
        "SEARCH_ENGINE_ERROR": "Dịch vụ tìm kiếm đang bị giới hạn, bạn có thể thử lại với câu hỏi ngắn gọn hơn.",
        "VALIDATION_ERROR": "Dữ liệu đầu vào không hợp lệ, vui lòng kiểm tra lại yêu cầu.",
        "API_ERROR": "Hệ thống AI đang quá tải, vui lòng chờ một lát rồi thử lại."
    }
    
    return {
        "status": "failed",
        "tool": tool_name,
        "reason": str(exc),
        "error_type": error_type,
        "suggestion": suggestions.get(error_type, "Đã có lỗi kỹ thuật xảy ra, vui lòng thử lại sau."),
        "retry_attempts": attempts,
        "max_retries": max_retries,
    }


# ============================================================
# ADK Callback: on_tool_error_callback
# ============================================================

def on_tool_error(tool, args, tool_context, error):
    """
    ADK on_tool_error_callback.

    Khi mot tool nem exception, callback nay se:
    1. Kiem tra loi co the retry khong.
    2. Neu co: retry voi Exponential Backoff.
    3. Neu khong hoac het retry: tra ve Structured Error Dict.

    Returns:
        dict: Ket qua thay the (ADK se dung dict nay lam tool result).
        None: De ADK xu ly loi (khong retry).
    """
    tool_name = getattr(tool, "name", str(tool))
    config = RETRY_CONFIG.get(tool_name, DEFAULT_RETRY)
    max_retries = config["max_retries"]
    base_delay = config["base_delay"]

    # Kiem tra loi co retryable khong
    if not isinstance(error, RETRYABLE_EXCEPTIONS):
        print(
            f"[NON-RETRYABLE] {tool_name}: "
            f"{type(error).__name__}: {error}"
        )
        return _build_error_dict(tool_name, error, 0, max_retries)

    # Retry voi Exponential Backoff
    func = getattr(tool, "func", None)
    if func is None:
        print(f"[RETRY SKIP] {tool_name}: Khong tim thay func de retry.")
        return _build_error_dict(tool_name, error, 0, max_retries)

    last_error = error
    for attempt in range(max_retries):
        delay = base_delay * (BACKOFF_FACTOR ** attempt)
        print(
            f"[RETRY {attempt + 1}/{max_retries}] "
            f"{tool_name}: {type(last_error).__name__}: {last_error}. "
            f"Cho {delay:.1f}s..."
        )
        time.sleep(delay)

        try:
            result = func(**args)
            print(f"[RETRY OK] {tool_name}: Thanh cong sau {attempt + 1} lan thu.")
            return {"result": result}
        except RETRYABLE_EXCEPTIONS as retry_err:
            last_error = retry_err
            continue
        except Exception as other_err:
            print(
                f"[NON-RETRYABLE] {tool_name}: "
                f"{type(other_err).__name__}: {other_err}"
            )
            return _build_error_dict(tool_name, other_err, attempt + 1, max_retries)

    # Het retry
    print(
        f"[RETRY FAILED] {tool_name}: Da thu {max_retries} lan. "
        f"Tra loi co cau truc."
    )
    return _build_error_dict(tool_name, last_error, max_retries, max_retries)
