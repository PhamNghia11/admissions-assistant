import { useState, useEffect, useRef } from "react";
import { ThemeProvider } from "./providers/ThemeProvider";
import { Sidebar } from "./components/Sidebar";
import { ChatMessage, type Message } from "./components/ChatMessage";
import { ChatInput } from "./components/ChatInput";
import { SettingsModal } from "./components/SettingsModal";
import { AuthModal } from "./components/AuthModal";
import { Header } from "./components/Header";
import { AuthProvider, useAuth } from "./providers/AuthProvider";
import { ProfileModal } from "./components/ProfileModal";
import { GoogleCallback } from "./components/GoogleCallback";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Toaster } from "sonner";

// Streaming response function from ADK Backend
async function* streamAdkResponse(userMessage: string, sessionId: string, userId: string) {
  const payload = {
    app_name: "my_agent",
    user_id: userId,
    session_id: sessionId,
    new_message: {
      role: "user",
      parts: [{ text: userMessage }]
    }
  };

  try {
    let response = await fetch('/api/run_sse', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (response.status === 404) {
      // Lazy Session Creation: create session on backend and retry
      await fetch(`/api/apps/my_agent/users/${userId}/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: sessionId })
      });
      // Retry sending message
      response = await fetch('/api/run_sse', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
    }

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('No response body');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    // Streaming State Machine: buffer text per-agent
    // Nếu agent emit text TRƯỚC function call → đó là pre-tool preamble → DROP
    // Nếu agent emit text SAU function response hoặc không có function call → DISPLAY
    const agentState: Record<string, { pendingText: string; hasCalledTool: boolean; hasRespondedTool: boolean }> = {};

    const getState = (author: string) => {
      if (!agentState[author]) {
        agentState[author] = { pendingText: '', hasCalledTool: false, hasRespondedTool: false };
      }
      return agentState[author];
    };

    // Post-process: thay * bullets bằng - bullets
    const cleanBullets = (text: string): string => {
      return text.replace(/^\s*\*\s/gm, '- ');
    };

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.substring(6).trim();
          if (dataStr) {
            try {
              const event = JSON.parse(dataStr);
              
              // Diagnostic logging (mở DevTools F12 → Console để xem)
              console.log('[SSE]', JSON.stringify({
                author: event.author,
                text: event.content?.parts?.some((p: any) => p.text) ? '✓' : '',
                fnCall: event.content?.parts?.some((p: any) => p.functionCall) ? '✓' : '',
                fnResp: event.content?.parts?.some((p: any) => p.functionResponse) ? '✓' : '',
                finish: event.finishReason || '',
                preview: event.content?.parts?.find((p: any) => p.text)?.text?.substring(0, 80) || ''
              }));

              if (!event.content || !event.content.parts) continue;

              const author = event.author || 'unknown';

              // Filter 1: Bỏ qua mọi event từ router_agent
              if (author === 'router_agent') continue;

              const state = getState(author);
              const hasFunctionCall = event.content.parts.some((p: any) => p.functionCall);
              const hasFunctionResponse = event.content.parts.some((p: any) => p.functionResponse);

              if (hasFunctionCall) {
                // Agent đang gọi tool → drop mọi pending text (pre-tool preamble)
                state.pendingText = '';
                state.hasCalledTool = true;
                state.hasRespondedTool = false;
              }

              if (hasFunctionResponse) {
                // Tool đã trả về → text tiếp theo là answer thật
                state.hasRespondedTool = true;
              }

              for (const part of event.content.parts) {
                if (part.text) {
                  const cleanedText = cleanBullets(part.text);
                  
                  if (state.hasRespondedTool || !state.hasCalledTool) {
                    // Agent đã nhận tool response, hoặc agent không gọi tool
                    // → Text này là answer thật, hiển thị ngay
                    // Flush pending text trước (nếu có)
                    if (state.pendingText) {
                      yield cleanBullets(state.pendingText);
                      state.pendingText = '';
                    }
                    yield cleanedText;
                  } else {
                    // Agent đã gọi tool nhưng chưa nhận response
                    // → Buffer text này (có thể là pre-tool preamble)
                    state.pendingText += cleanedText;
                  }
                }
              }
            } catch (e) {
              console.error("Error parsing JSON chunk:", e);
            }
          }
        }
      }
    }

    // Flush bất kỳ pending text còn sót
    for (const author of Object.keys(agentState)) {
      if (agentState[author].pendingText) {
        yield cleanBullets(agentState[author].pendingText);
      }
    }
  } catch (error) {
    console.error("Fetch error:", error);
    yield "\n\n**Lỗi:** Không thể kết nối đến Backend. Hãy đảm bảo Backend đang chạy (.\\start_app.ps1).";
  }
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const result = reader.result as string;
      const base64 = result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = error => reject(error);
  });
}

function getMimeTypeByExtension(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'pdf': return 'application/pdf';
    case 'docx': return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
    case 'doc': return 'application/msword';
    case 'txt': return 'text/plain';
    case 'csv': return 'text/csv';
    case 'png': return 'image/png';
    case 'jpg':
    case 'jpeg': return 'image/jpeg';
    case 'webp': return 'image/webp';
    default: return 'application/octet-stream';
  }
}

async function ensureSessionExists(sessionId: string, userId: string) {
  try {
    await fetch(`/api/apps/my_agent/users/${userId}/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId })
    });
  } catch (e) {
    console.error("Failed to ensure session exists:", e);
  }
}

async function uploadArtifact(file: File, sessionId: string, userId: string) {
  const base64Data = await fileToBase64(file);
  const payload = {
    filename: file.name,
    artifact: {
      inlineData: {
        data: base64Data,
        mimeType: file.type || getMimeTypeByExtension(file.name)
      }
    }
  };

  const res = await fetch(`/api/apps/my_agent/users/${userId}/sessions/${sessionId}/artifacts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    throw new Error(`Upload thất bại: ${res.statusText}`);
  }
}

interface ChatHistory {
  id: string;
  title: string;
  timestamp: Date;
  messages: Message[];
}

function AppContent() {
  const { user, guestSessionId, isLoading } = useAuth();
  const activeUserId = user ? user.email : (guestSessionId || "guest");
  const prevUserIdRef = useRef<string | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [backendStatus, setBackendStatus] = useState<"online" | "offline">("offline");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatHistory[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | undefined>(undefined);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Watch for Auth user transitions to clean state & secure chat session data
  useEffect(() => {
    if (prevUserIdRef.current && prevUserIdRef.current !== activeUserId) {
      setMessages([]);
      setCurrentChatId(undefined);
      setChatHistory([]);
      setPendingFiles([]);
      toast.info("Đã cập nhật phiên trò chuyện bảo mật mới.");
    }
    prevUserIdRef.current = activeUserId;
  }, [activeUserId]);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch('/api/list-apps');
        if (res.ok) {
          setBackendStatus("online");
        } else {
          setBackendStatus("offline");
        }
      } catch (e) {
        setBackendStatus("offline");
      }
    };
    checkStatus();
    const interval = setInterval(checkStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  if (isLoading) {
    return (
      <div className="h-screen w-screen bg-[#0f172a] flex flex-col items-center justify-center text-slate-100 text-sm">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin mb-4" />
        <span>Đang xác thực thông tin...</span>
      </div>
    );
  }

  const handleNewChat = () => {
    // Save current chat to history if it has messages
    if (messages.length > 0 && currentChatId) {
      const currentChat = chatHistory.find(c => c.id === currentChatId);
      if (currentChat) {
        setChatHistory(prev =>
          prev.map(c => c.id === currentChatId ? { ...c, messages } : c)
        );
      }
    }

    // Create new chat
    const newChatId = "chat-" + Date.now();
    setCurrentChatId(newChatId);
    setMessages([]);
    setChatHistory(prev => [
      {
        id: newChatId,
        title: "Cuộc trò chuyện mới",
        timestamp: new Date(),
        messages: [],
      },
      ...prev,
    ]);
  };

  const handleSelectChat = (chatId: string) => {
    // Save current chat before switching
    if (currentChatId && messages.length > 0) {
      setChatHistory(prev =>
        prev.map(c => c.id === currentChatId ? { ...c, messages } : c)
      );
    }

    // Load selected chat
    const selectedChat = chatHistory.find(c => c.id === chatId);
    if (selectedChat) {
      setCurrentChatId(chatId);
      setMessages(selectedChat.messages);
    }
  };

  const handleFileUpload = (file: File) => {
    if (file.size > 10 * 1024 * 1024) {
      alert("Kích thước tệp vượt quá 10MB. Vui lòng chọn tệp nhỏ hơn.");
      return;
    }
    setPendingFiles((prev) => [...prev, file]);
  };

  const handleRemovePendingFile = (index: number) => {
    setPendingFiles((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleReply = (message: Message) => {
    // Could implement reply functionality here
    console.log("Reply to:", message);
  };

  const handleEdit = (message: Message) => {
    // Could implement edit functionality here
    console.log("Edit:", message);
  };

  const handleDelete = (messageId: string) => {
    setMessages((prev) => prev.filter((msg) => msg.id !== messageId));
  };

  const handleCopy = (content: string) => {
    // Toast notification could be shown here
    console.log("Copied:", content);
  };

  const handleSendMessage = async (content: string) => {
    let activeChatId = currentChatId;
    // Create new chat if this is the first message
    if (messages.length === 0 && !currentChatId) {
      activeChatId = "chat-" + Date.now();
      setCurrentChatId(activeChatId);
      const firstWords = content.trim() ? content.split(" ").slice(0, 5).join(" ") : "Tài liệu tải lên";
      setChatHistory(prev => [
        {
          id: activeChatId as string,
          title: firstWords.length > 30 ? firstWords.substring(0, 30) + "..." : firstWords,
          timestamp: new Date(),
          messages: [],
        },
        ...prev,
      ]);
    }

    const sessionId = activeChatId || "default-session";
    setIsStreaming(true);

    // Copy pending files to upload
    const filesToUpload = [...pendingFiles];
    setPendingFiles([]); // Clear pending files immediately in UI

    let uploadError = null;
    const uploadedFilesMeta: Array<{ name: string; type: string; url?: string }> = [];

    if (filesToUpload.length > 0) {
      try {
        // 1. Ensure session is created on backend
        await ensureSessionExists(sessionId, activeUserId);

        // 2. Upload all files
        for (const file of filesToUpload) {
          await uploadArtifact(file, sessionId, activeUserId);
          uploadedFilesMeta.push({
            name: file.name,
            type: file.type,
            url: file.type.startsWith("image/") ? URL.createObjectURL(file) : undefined
          });
        }
      } catch (err: any) {
        console.error("Upload error:", err);
        uploadError = err.message || "Lỗi tải tệp tin";
      }
    }

    // Build user message
    const userMessage: Message = {
      id: "user-" + Date.now(),
      role: "user",
      content: content || (uploadedFilesMeta.length > 0 
        ? `Đã tải lên ${uploadedFilesMeta.length} tệp tin.` 
        : ""),
      timestamp: new Date(),
      files: uploadedFilesMeta.length > 0 ? uploadedFilesMeta : undefined
    };

    setMessages((prev) => [...prev, userMessage]);

    if (uploadError) {
      const errorMessage: Message = {
        id: "assistant-" + Date.now(),
        role: "assistant",
        content: `❌ **Lỗi khi tải tệp tin:** ${uploadError}. Vui lòng thử lại.`,
        timestamp: new Date()
      };
      setMessages((prev) => [...prev, errorMessage]);
      setIsStreaming(false);
      return;
    }

    // Create placeholder for streaming message
    const streamingMessageId = "assistant-" + Date.now();
    setMessages((prev) => [
      ...prev,
      {
        id: streamingMessageId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
      },
    ]);

    // Stream response
    try {
      let fullResponse = "";
      // Nếu prompt rỗng nhưng có file, tự tạo prompt phù hợp cho AI
      let promptToSend = content;
      if (!content.trim() && uploadedFilesMeta.length > 0) {
        const fileNames = uploadedFilesMeta.map(f => f.name).join(", ");
        promptToSend = `Tôi vừa tải lên các tệp: ${fileNames}. Bạn thấy chúng chưa và có thể giúp gì từ những tệp này?`;
      }

      for await (const chunk of streamAdkResponse(promptToSend, sessionId, activeUserId)) {
        fullResponse += chunk;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === streamingMessageId
              ? { ...msg, content: fullResponse }
              : msg
          )
        );
      }
    } catch (error) {
      console.error("Streaming error:", error);
    } finally {
      setIsStreaming(false);
    }
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        onNewChat={handleNewChat}
        onSettingsClick={() => setSettingsOpen(true)}
        backendStatus={backendStatus}
        chatHistory={chatHistory}
        onSelectChat={handleSelectChat}
        currentChatId={currentChatId}
        isCollapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      <div className="flex-1 flex flex-col">
        <Header
          onAuthClick={() => setAuthOpen(true)}
          onProfileClick={() => setProfileOpen(true)}
          onSettingsClick={() => setSettingsOpen(true)}
        />

        <div className="flex-1 flex flex-col overflow-hidden">
          {hasMessages ? (
            <>
              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto">
                <div className="w-full">
                  {messages.map((message) => (
                    <ChatMessage
                      key={message.id}
                      message={message}
                      onReply={handleReply}
                      onEdit={handleEdit}
                      onDelete={handleDelete}
                      onCopy={handleCopy}
                    />
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              </div>

              {/* Chat Input */}
              <ChatInput
                onSend={handleSendMessage}
                onFileSelect={handleFileUpload}
                disabled={isStreaming}
                centered={false}
                attachments={pendingFiles}
                onRemoveAttachment={handleRemovePendingFile}
              />
            </>
          ) : (
            /* Centered welcome view */
            <div className="flex-1 flex flex-col items-center justify-center p-8">
              <div className="text-center mb-12 max-w-2xl">
                <div className="w-20 h-20 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-6">
                  <span className="text-5xl">🤖</span>
                </div>
                <h1 className="text-4xl font-semibold mb-4">X-Agent</h1>
                <p className="text-lg text-muted-foreground mb-8">
                  Trợ lý AI thông minh của bạn. Sẵn sàng giúp đỡ với mọi câu hỏi.
                </p>

                {/* Quick suggestions */}
                <div className="grid grid-cols-2 gap-3 max-w-xl mx-auto mb-12">
                  <button
                    onClick={() => handleSendMessage("Bạn có thể làm gì?")}
                    className="p-4 rounded-xl border border-border hover:bg-accent text-left transition-colors cursor-pointer"
                  >
                    <p className="font-medium mb-1">💡 Khả năng</p>
                    <p className="text-sm text-muted-foreground">Bạn có thể làm gì?</p>
                  </button>
                  <button
                    onClick={() => handleSendMessage("Giải thích về AI")}
                    className="p-4 rounded-xl border border-border hover:bg-accent text-left transition-colors cursor-pointer"
                  >
                    <p className="font-medium mb-1">📚 Học tập</p>
                    <p className="text-sm text-muted-foreground">Giải thích về AI</p>
                  </button>
                  <button
                    onClick={() => handleSendMessage("Tạo ý tưởng sáng tạo")}
                    className="p-4 rounded-xl border border-border hover:bg-accent text-left transition-colors cursor-pointer"
                  >
                    <p className="font-medium mb-1">✨ Sáng tạo</p>
                    <p className="text-sm text-muted-foreground">Tạo ý tưởng sáng tạo</p>
                  </button>
                  <button
                    onClick={() => handleSendMessage("Giúp tôi viết code")}
                    className="p-4 rounded-xl border border-border hover:bg-accent text-left transition-colors cursor-pointer"
                  >
                    <p className="font-medium mb-1">💻 Lập trình</p>
                    <p className="text-sm text-muted-foreground">Giúp tôi viết code</p>
                  </button>
                </div>
              </div>

              {/* Centered Chat Input */}
              <div className="w-full max-w-3xl">
                <ChatInput
                  onSend={handleSendMessage}
                  onFileSelect={handleFileUpload}
                  disabled={isStreaming}
                  centered={true}
                  attachments={pendingFiles}
                  onRemoveAttachment={handleRemovePendingFile}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Modals */}
      <SettingsModal open={settingsOpen} onOpenChange={setSettingsOpen} />
      <AuthModal open={authOpen} onOpenChange={setAuthOpen} />
      <ProfileModal open={profileOpen} onOpenChange={setProfileOpen} />
    </div>
  );
}

export default function App() {
  const isCallback = window.location.pathname === "/auth/callback";

  return (
    <ThemeProvider>
      <Toaster richColors position="top-right" closeButton />
      <AuthProvider>
        {isCallback ? <GoogleCallback /> : <AppContent />}
      </AuthProvider>
    </ThemeProvider>
  );
}
