import { Bot, Plus, Circle, Settings, MessageSquare, PanelLeftClose } from "lucide-react";
import { useAuth } from "../providers/AuthProvider";

interface ChatHistory {
  id: string;
  title: string;
  timestamp: Date;
}

interface SidebarProps {
  onNewChat: () => void;
  onSettingsClick: () => void;
  backendStatus: "online" | "offline";
  chatHistory: ChatHistory[];
  onSelectChat: (chatId: string) => void;
  currentChatId?: string;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function Sidebar({
  onNewChat,
  onSettingsClick,
  backendStatus,
  chatHistory,
  onSelectChat,
  currentChatId,
  isCollapsed,
  onToggleCollapse
}: SidebarProps) {
  const { user } = useAuth();

  if (isCollapsed) {
    return (
      <div className="w-16 h-full bg-sidebar border-r border-sidebar-border flex flex-col items-center py-4 gap-4">
        <button
          onClick={onToggleCollapse}
          className="w-10 h-10 rounded-lg hover:bg-accent flex items-center justify-center"
          title="Mở sidebar"
        >
          <Bot className="w-6 h-6" />
        </button>
        <button
          onClick={onNewChat}
          className="w-10 h-10 rounded-lg bg-primary text-primary-foreground hover:opacity-90 flex items-center justify-center"
          title="Cuộc trò chuyện mới"
        >
          <Plus className="w-5 h-5" />
        </button>
      </div>
    );
  }

  return (
    <div className="w-80 h-full bg-sidebar border-r border-sidebar-border flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-sidebar-border space-y-4">
        <div className="flex items-center gap-3">
          <Bot className="w-8 h-8 text-blue-500" />
          <h1 className="text-2xl font-bold flex-1 tracking-tight">X-Agent</h1>
          <button
            onClick={onToggleCollapse}
            className="w-8 h-8 rounded-xl hover:bg-accent flex items-center justify-center cursor-pointer transition-all"
            title="Đóng sidebar"
          >
            <PanelLeftClose className="w-5 h-5" />
          </button>
        </div>

        <button
          onClick={onNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-primary text-primary-foreground hover:opacity-90 transition-opacity font-semibold cursor-pointer text-sm"
        >
          <Plus className="w-4 h-4" />
          <span>Cuộc trò chuyện mới</span>
        </button>
      </div>

      {/* Chat History */}
      <div className="flex-1 p-4 overflow-y-auto">
        <p className="text-xs font-medium text-muted-foreground px-2 mb-2">LỊCH SỬ</p>
        <div className="space-y-1">
          {chatHistory.length === 0 ? (
            <p className="text-sm text-muted-foreground px-2 py-4 text-center">
              Chưa có cuộc trò chuyện nào
            </p>
          ) : (
            chatHistory.map((chat) => (
              <button
                key={chat.id}
                onClick={() => onSelectChat(chat.id)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-accent transition-colors text-left ${
                  currentChatId === chat.id ? "bg-accent" : ""
                }`}
              >
                <MessageSquare className="w-4 h-4 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">{chat.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {chat.timestamp.toLocaleDateString("vi-VN")}
                  </p>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Bottom Section */}
      <div className="p-4 border-t border-sidebar-border space-y-3">
        {/* Backend Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900/40 border border-slate-800/40 text-xs">
          <Circle
            className={`w-1.5 h-1.5 ${
              backendStatus === "online" ? "fill-green-500 text-green-500" : "fill-red-500 text-red-500"
            } animate-pulse`}
          />
          <span className="text-[11px] text-slate-400 font-medium">
            {backendStatus === "online" ? "Trực tuyến" : "Ngoại tuyến"}
          </span>
        </div>

        {/* User Card & Settings */}
        <div className="flex items-center justify-between gap-3 p-2 rounded-xl bg-slate-900/60 border border-slate-800/80">
          {user ? (
            <div className="flex items-center gap-2 min-w-0 flex-1">
              {user.avatar_url ? (
                <img 
                  src={user.avatar_url} 
                  alt={user.name} 
                  className="w-8 h-8 rounded-lg object-cover ring-1 ring-slate-800"
                />
              ) : (
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-650 flex items-center justify-center text-white font-extrabold text-xs shadow-sm">
                  {user.name.charAt(0).toUpperCase()}
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="text-[9px] font-bold text-slate-500 uppercase tracking-wider leading-none mb-0.5">Tài khoản</p>
                <p className="text-xs font-semibold text-slate-200 truncate leading-snug">{user.name}</p>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <div className="w-8 h-8 rounded-lg bg-blue-950/40 border border-blue-500/20 flex items-center justify-center text-blue-400">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-blue-400 truncate leading-snug">Chế độ Guest</p>
                <p className="text-[9px] text-slate-500 truncate leading-none">Dùng thử</p>
              </div>
            </div>
          )}

          <button
            onClick={onSettingsClick}
            className="w-8 h-8 rounded-lg hover:bg-slate-800 flex items-center justify-center text-slate-400 hover:text-slate-200 transition-colors border border-transparent hover:border-slate-700/60 cursor-pointer flex-shrink-0"
            title="Cài đặt"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
