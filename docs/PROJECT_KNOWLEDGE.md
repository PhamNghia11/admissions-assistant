# PROJECT KNOWLEDGE - X-Agent

> Source of truth for the current repo state.
> Updated: 29/05/2026 - launcher, auth server, and ADK flow synced.

## 1. Current Runtime

- Primary launcher: `start_app.ps1`
- `start_app.ps1` starts:
  - `scripts/auto_watcher.py`
  - `auth_server.py` on `127.0.0.1:8001`
  - ADK Web on the requested port (`8000` by default)
- `start_ui.ps1` is optional and only runs the standalone React UI for local frontend development.

## 2. Repository Map

> Đọc phần này từ trên xuống dưới. Mỗi file đều có chú thích ngắn ngay bên cạnh.

```text
D:\agent
|-- start_app.ps1                  # Trình khởi chạy chính: bật auth server, auto watcher và ADK Web
|-- start_ui.ps1                   # Công cụ chạy riêng giao diện React để dev frontend
|-- auth_server.py                 # Dịch vụ auth FastAPI cho OTP email và Google OAuth
|-- requirements.txt               # Danh sách dependency Python cho backend
|-- .env                           # Secret cục bộ và cấu hình riêng của máy
|-- .env.example                   # Mẫu cấu hình an toàn, không chứa secret
|-- ARCHITECTURE.md                # Sơ đồ luồng hệ thống và DAG xử lý
|-- PROJECT_KNOWLEDGE.md           # Bản đồ học kiến thức của repo
|-- adk_help.txt                   # Ghi chú và mẹo dùng ADK
|
|-- my_agent/
|   |-- agent.py                   # Ghép các agent ADK và đăng ký tools/module
|   |-- application/
|   |   |-- assistant_application.py # Chứa các tool và phần điều phối ứng dụng
|   |-- auth/
|   |   |-- router.py              # Endpoint auth và logic đăng ký/đăng nhập
|   |   |-- database.py            # Lưu user, OTP và state OAuth trong SQLite
|   |   |-- google_oauth.py        # Đổi code Google lấy token và userinfo
|   |   |-- jwt_service.py         # Hàm tạo và kiểm tra JWT
|   |   |-- otp_service.py         # Sinh OTP và gửi email xác thực
|   |   |-- models.py              # Schema Pydantic cho request/response auth
|   |-- core/
|   |   |-- rag_engine.py          # Tìm kiếm RAG lai: vector + BM25 + độ mới
|   |   |-- guardrail.py           # Kiểm tra an toàn, telemetry và chống bịa
|   |   |-- retry_manager.py       # Callback retry cho lỗi tạm thời
|   |   |-- cache_manager.py       # Cache kết quả web search trên đĩa
|   |   |-- environment.py         # Nạp biến môi trường và cấu hình chạy
|   |-- modules/
|   |   |-- base.py                # Lớp nền dùng chung cho các module kiến thức
|   |   |-- legal_module.py        # Tra cứu kiến thức pháp luật
|   |   |-- admissions_module.py   # Tra cứu kiến thức tuyển sinh
|   |   |-- health_module.py       # Tra cứu kiến thức y tế
|   |   |-- wiki_module.py         # Tra cứu kiến thức tổng quát / wiki
|   |   |-- memory_module.py       # Tra cứu bộ nhớ cá nhân và sở thích người dùng
|   |-- services/
|   |   |-- web_service.py         # Dịch vụ tìm kiếm web nhanh và sâu
|   |-- data/                      # Dữ liệu đã index, cache và bộ nhớ
|   |   |-- admissions/            # Dữ liệu LanceDB cho mảng tuyển sinh
|   |   |-- health/                # Dữ liệu LanceDB cho mảng y tế
|   |   |-- legal/                 # Dữ liệu LanceDB cho mảng pháp luật
|   |   |-- memory/                # Kho lưu bộ nhớ cá nhân
|   |   |-- wiki/                  # Kho kiến thức tổng quát
|   |   |-- cache/                 # File JSON cache kết quả web search
|
|-- ui-agent/
|   |-- src/app/App.tsx            # Khung React chính, SSE stream, upload và state ứng dụng
|   |-- src/app/providers/AuthProvider.tsx # Quản lý trạng thái đăng nhập và nạp lại session
|   |-- src/app/providers/ThemeProvider.tsx # Trạng thái giao diện sáng/tối
|   |-- src/app/components/AuthModal.tsx # Hộp thoại đăng nhập/đăng ký
|   |-- src/app/components/GoogleCallback.tsx # Trang callback cho Google OAuth
|   |-- src/app/components/ChatInput.tsx # Ô nhập chat và hàng đợi file đính kèm
|   |-- src/app/components/ChatMessage.tsx # Hiển thị tin nhắn, markdown và bảng
|   |-- src/app/components/Header.tsx # Thanh trên cùng và menu người dùng
|   |-- src/app/components/ProfileModal.tsx # Xem hồ sơ và thao tác tài khoản
|   |-- src/app/components/SettingsModal.tsx # Phần cài đặt ứng dụng
|   |-- src/app/components/Sidebar.tsx # Lịch sử chat và điều hướng
|   |-- src/app/components/ThemeToggle.tsx # Nút chuyển giao diện sáng/tối
|   |-- src/styles/                 # Style nền, font và token thiết kế
|
|-- scripts/
|   |-- auto_watcher.py            # Theo dõi thư mục nóng và tự nạp dữ liệu
|   |-- auto_pipeline.ps1          # Pipeline nạp dữ liệu hàng loạt
|   |-- ingest_admissions.py       # Làm mới bộ dữ liệu tuyển sinh vào RAG (BUV, BKA, BMU)
|   |-- organize_gdu_files.py      # Chuẩn hóa dữ liệu thô GDU vào cấu trúc 4 cấp của trường
|   |-- ingest_gdu_classified.py   # Phân tích Word, PDF, Excel, Q&A GDU và nạp nối tiếp vào DB
|   |-- db_summary.py              # Thống kê số lượng chunks tuyển sinh của từng trường trong DB
|   |-- db_viewer.py               # Công cụ xem dữ liệu trong DB (hỗ trợ in tiếng Việt an toàn)
|-- openapi_full.json              # Đặc tả API để tích hợp / debug bên ngoài
|-- workflow_diagram.md.resolved   # Ghi chú workflow cũ
```

## 3. Core Runtime Files

- `start_app.ps1`: primary launcher for ADK Web, auth server, and auto ingest.
- `auth_server.py`: FastAPI auth service for email OTP and Google OAuth.
- `my_agent/agent.py`: defines the ADK agent graph and registers tools.
- `my_agent/application/assistant_application.py`: keeps tool handlers and app orchestration together.
- `my_agent/core/guardrail.py`: safety and telemetry callbacks for tool execution.
- `my_agent/core/retry_manager.py`: retry logic for transient tool failures.
- `my_agent/core/rag_engine.py`: hybrid RAG engine used by domain modules.
- `my_agent/core/cache_manager.py`: stores web search cache on disk.
- `my_agent/modules/*`: specialist knowledge modules.
- `my_agent/services/web_service.py`: quick/deep web search helpers.

## 4. Auth Flow

### Email OTP

1. `ui-agent/src/app/components/AuthModal.tsx` calls `POST /auth/send-otp`.
2. `my_agent/auth/router.py` checks the `action` value (`login` or `register`).
3. `my_agent/auth/database.py` stores OTPs, rate limits, and email status.
4. `POST /auth/verify-otp` creates or verifies the user, then returns JWT.
5. `ui-agent/src/app/providers/AuthProvider.tsx` stores `auth_token` in localStorage and updates browser state.

### Google OAuth

1. `AuthModal.tsx` calls `GET /auth/google/url`.
2. Browser redirects to Google, then returns to `/auth/callback`.
3. `ui-agent/src/app/components/GoogleCallback.tsx` sends `code` + `state` to `POST /auth/google/callback`.
4. `my_agent/auth/router.py` verifies state, exchanges token, fetches userinfo, and creates or links the account.
5. `AuthProvider.tsx` stores token and hydrates user state.

### Auth Rules

- Google-only accounts must sign in with Google.
- Email accounts linked to Google can still use OTP email if the original provider is `email`.
- `GoogleCallback.tsx` does not auto-redirect on error; the user must go back to login and try again.

## 5. AI / Request Flow

```text
User input
  -> ADK Web / React UI
  -> router_agent
  -> rag_agent | tool_agent | vision_agent | answer_agent
  -> streamed response back to UI
```

- `router_agent` classifies the intent.
- `rag_agent` uses `RAGManager.search()` to pull context from LanceDB. Nó sẽ ưu tiên tìm trong database nội bộ trước, chỉ khi thông tin bị thiếu mới gọi thêm `web_deep_search` để bổ sung (giúp tiết kiệm token và thời gian).
- `tool_agent` handles web search, memory, and external tools.
- `vision_agent` reads uploaded files from the ADK artifact store.
- `answer_agent` writes the final answer.
- Frontend `App.tsx` keeps the SSE state machine, pending files, and `pendingText` buffer.

## 6. Commands

| Command | Purpose |
|---|---|
| `.\start_app.ps1` | Start the primary system (ADK Web + auth server + auto ingest) |
| `.\start_app.ps1 8002` | Start ADK Web on a different port; avoid `8001` because auth server uses it |
| `.\start_ui.ps1` | Optional React UI dev server |
| `pip install -r requirements.txt` | Install Python dependencies |
| `npm run build` in `ui-agent` | Build the frontend |

## 7. Source of Truth

| File | Role |
|---|---|
| `start_app.ps1` | Primary launcher |
| `auth_server.py` | Auth microservice entrypoint |
| `my_agent/agent.py` | ADK agent definitions |
| `my_agent/auth/router.py` | Auth endpoints and policy |
| `my_agent/auth/database.py` | SQLite auth storage |
| `my_agent/core/guardrail.py` | Guardrail and telemetry callbacks |
| `my_agent/core/retry_manager.py` | Retry callbacks |
| `my_agent/core/rag_engine.py` | Hybrid RAG engine |
| `my_agent/application/assistant_application.py` | Tool implementations |
| `ui-agent/src/app/App.tsx` | React app shell and SSE streaming |
| `ui-agent/src/app/components/AuthModal.tsx` | Login/register modal |
| `ui-agent/src/app/components/GoogleCallback.tsx` | Google OAuth callback page |
| `ui-agent/src/app/providers/AuthProvider.tsx` | Browser auth state |
| `ui-agent/src/app/components/ChatInput.tsx` | Chat input and attachment queue |
| `ui-agent/src/app/components/ChatMessage.tsx` | Markdown rendering and message UI |

## 8. Notes

- `start_app.ps1` always spawns the auth server on port `8001`.
- The ADK web port is configurable, but `8001` should not be used for ADK because it conflicts with auth.
- `Toaster` is mounted in `ui-agent/src/app/App.tsx` so auth feedback is visible both as toast and inline notice.
- Keep `.env` and `.env.example` in sync when auth or model settings change.
