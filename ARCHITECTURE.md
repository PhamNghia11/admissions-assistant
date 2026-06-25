# X-Agent Architecture

## 1. Tổng quan

```
User → ADK Web → router_agent → [rag_agent | tool_agent | vision_agent | answer_agent] → User
     ↑
[File Upload] → POST /artifacts → ADK Artifact Store → vision_agent (load_artifacts_tool → parse_document)
```

`start_app.ps1` là launcher chính. `start_ui.ps1` chỉ là UI dev helper khi cần chạy React riêng.

**Cập nhật lần cuối:** 29/05/2026 — Đồng bộ auth server + launcher chính + file upload ADK

**Nếu đang học dự án lần đầu, nên đọc theo thứ tự này:**
1. `start_app.ps1` - biết hệ thống được khởi động thế nào.
2. `auth_server.py` và `my_agent/auth/router.py` - hiểu luồng đăng nhập/OTP/Google.
3. `my_agent/agent.py` - hiểu graph agent và cách tool được gắn vào.
4. `UI agent/src/app/App.tsx` - hiểu SSE stream và vòng đời UI.
5. `UI agent/src/app/providers/AuthProvider.tsx` - hiểu auth state trong browser.

---

## 2. Sơ đồ hệ thống

```mermaid
flowchart TD
    User((Người dùng))
    
    subgraph Frontend ["UI Agent (React)"]
        direction TB
        Web[ADK Web UI]
        Stream[SSE Streaming Buffer]
        FileQueue["pendingFiles Queue\n(ChatInput.tsx)"]
        MDRenderer["Markdown + Table Renderer\n(ChatMessage.tsx)"]
    end

    subgraph ArtifactStore ["ADK Artifact Store (.adk/artifacts)"]
        ArtifactAPI["POST /artifacts\n(Base64 Upload)"]
        FileStore[("Tệp lưu trữ\ntheo session/user")]
    end

    subgraph Router ["router_agent - Điều phối"]
        R{Phân loại ý định}
    end

    subgraph Workers ["Worker Agents - Tool-First"]
        direction LR
        RAG["rag_agent<br/>Kiến thức nội bộ"]
        Tool["tool_agent<br/>Internet Search"]
        Vision["vision_agent<br/>Đọc tài liệu + Ảnh"]
    end

    Answer["answer_agent<br/>Xã giao"]

    subgraph Guardrail ["Guardrail Layer (tool_agent)"]
        G_Before["before_agent\nReset cờ"]
        G_BeforeTool["before_tool\nRate Limit + Cache Hit"]
        G_AfterTool["after_tool\nLatency + Cache Write"]
        G_AfterModel["after_model\nÉp gọi tool"]
        G_AfterAgent["after_agent\nTrace Log"]
    end

    subgraph Retry ["ADK Callback - on_tool_error"]
        RetryLogic["Retry Manager<br/>Exponential Backoff"]
    end

    subgraph Tools ["Công cụ (FunctionTool)"]
        direction LR
        T_Legal[search_legal]
        T_Wiki[search_wiki]
        T_Admissions[search_admissions]
        T_Health[search_health]
        T_Web[web_search]
        T_Deep[web_deep_search]
        T_URL[browse_url]
        T_Mem[save/recall_memory]
        T_Doc[parse_document]
        T_LoadArtifacts[load_artifacts_tool]
    end

    subgraph Data ["Dữ liệu"]
        LanceDB[(LanceDB Vector)]
        Cache[(Cache Layer\nTTL 1h)]
        DuckDuckGo[DuckDuckGo API]
    end

    %% Luồng chính
    User <--> Web
    Web --> Stream
    Stream <--> R

    %% File Upload Flow
    FileQueue -->|"Base64 + MIME type"| ArtifactAPI
    ArtifactAPI --> FileStore
    FileStore -.->|"load_artifact(filename)"| T_Doc
    FileStore -.->|"list_artifacts()"| T_LoadArtifacts

    R -->|"Pháp luật, Tuyển sinh,<br/>Y tế"| RAG
    R -->|"Giá cả, Tin tức, Thời sự, So sánh, Top,<br/>Lịch sử, Khoa học, Văn hóa"| Tool
    R -->|"Đọc file PDF/Word/Ảnh"| Vision
    R -->|"Chào hỏi, Cảm ơn"| Answer

    %% Worker → Tools
    RAG --> T_Legal & T_Wiki & T_Admissions & T_Health & T_Deep
    Vision --> T_LoadArtifacts
    T_LoadArtifacts -->|"Thông báo LLM có file"| Vision
    Vision --> T_Doc
    
    %% Guardrail interception cho tool_agent
    Tool -.-> G_Before
    Tool -.-> G_BeforeTool
    Tool -.-> G_AfterTool
    Tool -.-> G_AfterModel
    Tool -.-> G_AfterAgent
    G_AfterModel -->|"Ép gọi web_search"| T_Web
    G_BeforeTool -->|"Cache Hit: return cached"| Cache
    G_AfterTool -->|"Cache Write"| Cache
    Tool --> T_Web & T_Deep & T_URL & T_Mem

    %% Tools → Data
    T_Legal & T_Wiki & T_Admissions & T_Health --> Cache --> LanceDB
    T_Web & T_Deep --> DuckDuckGo
    T_Mem --> LanceDB

    %% Retry callback
    T_Web & T_Deep & T_Legal -.->|"Exception"| RetryLogic
    RetryLogic -.->|"Re-invoke func"| T_Web & T_Deep & T_Legal

    %% Response
    RAG & Tool & Vision & Answer -->|"Response + Nguồn"| Web
    Web -->|"Markdown + Bảng"| MDRenderer
```

---

## 3. Luồng chi tiết (Request Flow)

```mermaid
sequenceDiagram
    actor User
    participant Router as router_agent
    participant Tool as tool_agent
    participant BT as before_tool_callback
    participant WebSearch as web_search()
    participant Cache as Cache (disk)
    participant AA as after_agent_callback
    participant Retry as on_tool_error_callback
    participant LLM as Gemini Flash

    User->>Router: "giá đất hôm nay"
    Router->>Router: Phân loại → Giá cả → tool_agent
    Router->>Tool: transfer_to_agent

    Tool->>LLM: Quyết định gọi tool nào
    LLM-->>Tool: Gọi web_search("giá đất hôm nay")

    Tool->>BT: before_tool_callback(web_search, args)
    BT->>BT: Kiểm tra rate limit (≤ 5 lần)
    BT->>Cache: get(query, ttl=1h)

    alt Cache Hit
        Cache-->>BT: Kết quả cũ (str)
        BT-->>Tool: return cached (bỏ qua API)
    else Cache Miss
        BT-->>Tool: return None (chạy tool thực tế)
        Tool->>WebSearch: web_search("giá đất hôm nay")

        alt Thành công
            WebSearch-->>Tool: Kết quả tìm kiếm (str)
            Note over Tool: after_tool: ghi latency<br/>lưu cache
            Tool->>Cache: set(query, result, ttl=1h)
            Tool-->>User: "Theo [nguồn](URL), giá đất..."
        end

        alt Lỗi mạng (DDGSException)
            WebSearch--xTool: Exception!
            Tool->>Retry: on_tool_error(tool, args, ctx, error)
            Retry->>Retry: Kiểm tra retryable? ✅
            loop Retry 1→3 (Exponential Backoff)
                Retry->>WebSearch: Re-invoke func(**args)
                alt Thành công
                    WebSearch-->>Retry: Kết quả
                    Retry-->>Tool: {result: "..."}
                    Tool-->>User: "Theo [nguồn](URL), ..."
                end
                alt Vẫn lỗi
                    WebSearch--xRetry: Exception!
                    Retry->>Retry: Chờ delay * 2
                end
            end
            Retry-->>Tool: {status: "failed", ...}
            Tool-->>User: "Hệ thống đang bận, vui lòng thử lại sau."
        end
    end

    Tool->>AA: after_agent_callback()
    AA->>AA: In [TRACE LOG]: số lần gọi, latency từng tool, tổng TG
```

---

## 4. Cấu hình Retry (ADK Callback)

| Tool | Max Retries | Base Delay | Backoff |
|------|-------------|------------|---------|
| web_search | 3 | 1.0s | ×2 |
| web_deep_search | 3 | 1.0s | ×2 |
| browse_url | 3 | 1.0s | ×2 |
| search_legal | 2 | 0.5s | ×2 |
| search_wiki | 2 | 0.5s | ×2 |
| search_admissions | 2 | 0.5s | ×2 |
| search_health | 2 | 0.5s | ×2 |
| save_memory | 2 | 0.5s | ×2 |
| recall_memory | 2 | 0.5s | ×2 |

**Retryable Exceptions:**
`ConnectionError`, `TimeoutError`, `OSError`, `DDGSException`, `RatelimitException`, `httpx.ConnectError`, `httpx.TimeoutException`

---

## 5. Key Features

1. **Tool-First Architecture**: Worker agents BẮT BUỘC gọi tool trước khi trả lời → chống hallucination.
2. **ADK Callback Retry**: `on_tool_error_callback` xử lý retry ở tầng framework, tool functions sạch sẽ.
3. **Hybrid RAG**: Vector Search + BM25 + Recency Boost.
4. **Deep Web Search**: Tự động đọc chi tiết top 3 trang web.
5. **Auto Escalation**: `web_search` rỗng → tự động gọi `web_deep_search`.
6. **Episodic Memory**: Phân loại ký ức (Profile, Preference, Reflection).
7. **Rate Limiting**: Chặn lần gọi tool > 5 lần/lượt tránh vòng lặp vô hạn.
8. **Web Search Cache**: Lưu kết quả `web_search`/`web_deep_search` vào disk cache TTL 1 giờ, tiết kiệm API call khi cùng query.
9. **Telemetry / Trace Log**: Mỗi lượt agent kết thúc in `[TRACE LOG]` tổng kết latency từng tool và tổng thời gian chạy.
10. **File Upload thực tế (ADK Artifacts)** *(mới)*: Người dùng đính kèm tệp tin → Frontend Base64 hóa và upload lên ADK Artifact Store qua `POST /artifacts` trước khi gửi câu hỏi. `vision_agent` dùng `load_artifacts_tool` để nhận diện tệp, sau đó gọi `parse_document` để trích xuất nội dung PDF/DOCX/TXT/CSV.
11. **Markdown & Bảng Premium Renderer** *(mới)*: `ChatMessage.tsx` tích hợp bộ parser thuần Regex, tự động convert bảng Markdown thô thành bảng HTML Premium (bo góc, bóng mờ, hàng xen kẽ màu, hover hiệu ứng). Hỗ trợ thêm: in đậm, in nghiêng, inline code, danh sách, tiêu đề phụ.

---

## 6. Source-of-Truth Files

| File | Vai trò |
|------|---------|
| `start_app.ps1` | Launcher chính |
| `auth_server.py` | FastAPI auth service (OTP + Google OAuth) |
| `my_agent/auth/router.py` | Auth endpoints, OTP policy, Google callback |
| `my_agent/auth/database.py` | SQLite users / OTP / OAuth state store |
| `my_agent/agent.py` | Định nghĩa Agents + Instructions + đăng ký `load_artifacts_tool` cho `vision_agent` |
| `my_agent/core/guardrail.py` | Lớp khiên chống Hallucination + Telemetry (**5 ADK Callbacks** cho `tool_agent`) |
| `my_agent/core/retry_manager.py` | ADK Callback retry (`on_tool_error`) |
| `my_agent/core/cache_manager.py` | Cache kết quả web search (TTL 1h, disk-based) |
| `my_agent/application/assistant_application.py` | Tool functions — `parse_document` dùng `tool_context.load_artifact()` (async, không hardcode path) |
| `my_agent/core/rag_engine.py` | Hybrid Search + Recency |
| `my_agent/modules/memory_module.py` | Categorized Memory |
| `my_agent/services/web_service.py` | Quick & Deep Web Search |
| `ui-agent/src/app/App.tsx` | Frontend SSE Streaming State Machine + File Upload (Base64 → `/artifacts`) |
| `ui-agent/src/app/components/AuthModal.tsx` | Modal đăng nhập / đăng ký / Google |
| `ui-agent/src/app/components/GoogleCallback.tsx` | Trang callback Google OAuth |
| `ui-agent/src/app/providers/AuthProvider.tsx` | Token / guest session / auth state trong browser |
| `ui-agent/src/app/components/ChatInput.tsx` | Khung nhập chat + hàng đợi file đính kèm (`pendingFiles`) với preview thumbnail |
| `ui-agent/src/app/components/ChatMessage.tsx` | Render tin nhắn + Markdown Parser + **Premium Table Renderer** |

---

## 7. Operational Notes

- **Launcher chính**: `.\start_app.ps1`
- **UI dev helper**: `.\start_ui.ps1` chỉ dùng khi cần chạy frontend React độc lập
- **Time Awareness**: AI được inject thời gian thực.
- **Citation Rule**: Bắt buộc trích dẫn `[Theo nguồn](URL)` trong mọi câu trả lời.
- **Hot Folder**: Thả file vào `hot_folder/<topic>/` để AI tự học.

---

## 8. Frontend SSE Streaming Architecture

Giao diện React hứng luồng dữ liệu Server-Sent Events (SSE) `/api/run_sse` thông qua cơ chế đọc stream của trình duyệt, được cấu trúc như sau:

```mermaid
sequenceDiagram
    participant Backend as ADK Backend (SSE API)
    participant App as UI Agent (App.tsx)
    participant UI as Giao diện hiển thị (ChatMessage)

    Backend->>App: "data: { author: 'router_agent', ... }"
    Note over App: Bỏ qua router_agent (không hiển thị)

    Backend->>App: "data: { author: 'tool_agent', parts: [{ text: 'Đang tìm kiếm...' }] }"
    Note over App: tool_agent gọi tool? ✅<br/>Buffer text vào pendingText (preamble)

    Backend->>App: "data: { author: 'tool_agent', parts: [{ functionCall: ... }] }"
    Note over App: Phát sinh functionCall!<br/>Clean pendingText = "" (Xóa bỏ preamble)

    Backend->>App: "data: { author: 'tool_agent', parts: [{ functionResponse: ... }] }"
    Note over App: Nhận functionResponse!<br/>hasRespondedTool = true

    Backend->>App: "data: { author: 'tool_agent', parts: [{ text: 'Giá vàng hôm nay...' }] }"
    App->>UI: Hiển thị trực tiếp: "Giá vàng hôm nay..."
```

**Tính Năng Nổi Bật:**
1. **Preamble Removal**: Ngăn chặn các câu mồi/rào đón rườm rà của mô hình ngôn ngữ lớn (ví dụ: *"Để tôi tra cứu..."*) hiển thị lên UI, mang lại trải nghiệm gọn gàng, tập trung.
2. **Multi-Agent State Separation**: Mỗi Agent (`author`) có một State riêng độc lập, tránh xung đột dữ liệu và giúp việc chuyển đổi hiển thị luồng giữa các Agent vô cùng mượt mà.
3. **No UI Freezing**: Cơ chế đệm và xả buffer thông minh triệt tiêu hoàn toàn lỗi kẹt UI hoặc treo hiển thị `"..."` thường thấy ở các giải pháp streaming thông thường.
