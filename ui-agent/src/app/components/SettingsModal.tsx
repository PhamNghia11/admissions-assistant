import * as Dialog from "@radix-ui/react-dialog";
import { X, Settings, Zap, Database, Shield, Bell } from "lucide-react";
import { useState } from "react";
import { useTheme } from "next-themes";

interface SettingsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SettingsModal({ open, onOpenChange }: SettingsModalProps) {
  const [activeTab, setActiveTab] = useState("general");
  const { theme, setTheme } = useTheme();

  const tabs = [
    { id: "general", label: "Chung", icon: Settings },
    { id: "model", label: "Mô hình AI", icon: Zap },
    { id: "data", label: "Dữ liệu", icon: Database },
    { id: "privacy", label: "Riêng tư", icon: Shield },
    { id: "notifications", label: "Thông báo", icon: Bell },
  ];

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-background border border-border rounded-2xl shadow-lg w-[90vw] max-w-3xl max-h-[85vh] overflow-hidden z-50">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <Dialog.Title className="text-xl font-semibold">Cài đặt</Dialog.Title>
            <Dialog.Close asChild>
              <button className="w-8 h-8 rounded-lg hover:bg-accent flex items-center justify-center">
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>

          {/* Content */}
          <div className="flex h-[calc(85vh-100px)]">
            {/* Sidebar */}
            <div className="w-48 border-r border-border p-4 space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                      activeTab === tab.id
                        ? "bg-accent text-accent-foreground"
                        : "hover:bg-accent/50"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm">{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Main content */}
            <div className="flex-1 overflow-y-auto p-6">
              {activeTab === "general" && (
                <div className="space-y-6">
                  <div>
                    <h3 className="font-medium mb-3">Giao diện</h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">Chế độ hiển thị</p>
                          <p className="text-sm text-muted-foreground">Chọn chế độ sáng hoặc tối</p>
                        </div>
                        <select
                          value={theme}
                          onChange={(e) => setTheme(e.target.value)}
                          className="px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                        >
                          <option value="light">Sáng</option>
                          <option value="dark">Tối</option>
                          <option value="system">Theo hệ thống</option>
                        </select>
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">Ngôn ngữ</p>
                          <p className="text-sm text-muted-foreground">Chọn ngôn ngữ giao diện</p>
                        </div>
                        <select className="px-3 py-2 rounded-lg border border-border bg-background text-foreground">
                          <option>Tiếng Việt</option>
                          <option>English</option>
                        </select>
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">Tự động lưu lịch sử</p>
                          <p className="text-sm text-muted-foreground">Lưu cuộc trò chuyện tự động</p>
                        </div>
                        <input type="checkbox" defaultChecked className="w-5 h-5" />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "model" && (
                <div className="space-y-6">
                  <div>
                    <h3 className="font-medium mb-3">Cấu hình mô hình AI</h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block font-medium mb-2">Mô hình</label>
                        <select className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground">
                          <option>GPT-4 Turbo</option>
                          <option>GPT-4</option>
                          <option>GPT-3.5 Turbo</option>
                          <option>Claude 3 Opus</option>
                          <option>Claude 3 Sonnet</option>
                        </select>
                      </div>

                      <div>
                        <label className="block font-medium mb-2">Temperature: 0.7</label>
                        <input type="range" min="0" max="1" step="0.1" defaultValue="0.7" className="w-full" />
                        <p className="text-sm text-muted-foreground mt-1">
                          Độ sáng tạo của AI (0 = chính xác, 1 = sáng tạo)
                        </p>
                      </div>

                      <div>
                        <label className="block font-medium mb-2">Max Tokens</label>
                        <input
                          type="number"
                          defaultValue="2048"
                          className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground"
                        />
                        <p className="text-sm text-muted-foreground mt-1">
                          Độ dài tối đa của câu trả lời
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "data" && (
                <div className="space-y-6">
                  <div>
                    <h3 className="font-medium mb-3">Quản lý dữ liệu</h3>
                    <div className="space-y-4">
                      <button className="w-full px-4 py-3 rounded-lg border border-border hover:bg-accent text-left">
                        <p className="font-medium">Xuất lịch sử chat</p>
                        <p className="text-sm text-muted-foreground">Tải xuống tất cả cuộc trò chuyện</p>
                      </button>

                      <button className="w-full px-4 py-3 rounded-lg border border-destructive text-destructive hover:bg-destructive/10 text-left">
                        <p className="font-medium">Xóa tất cả dữ liệu</p>
                        <p className="text-sm">Xóa vĩnh viễn lịch sử và cài đặt</p>
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "privacy" && (
                <div className="space-y-6">
                  <div>
                    <h3 className="font-medium mb-3">Quyền riêng tư & Bảo mật</h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">Mã hóa end-to-end</p>
                          <p className="text-sm text-muted-foreground">Bảo vệ dữ liệu của bạn</p>
                        </div>
                        <input type="checkbox" defaultChecked className="w-5 h-5" />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">Chia sẻ dữ liệu cải thiện AI</p>
                          <p className="text-sm text-muted-foreground">Giúp cải thiện chất lượng</p>
                        </div>
                        <input type="checkbox" className="w-5 h-5" />
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === "notifications" && (
                <div className="space-y-6">
                  <div>
                    <h3 className="font-medium mb-3">Thông báo</h3>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">Thông báo desktop</p>
                          <p className="text-sm text-muted-foreground">Nhận thông báo khi có phản hồi</p>
                        </div>
                        <input type="checkbox" defaultChecked className="w-5 h-5" />
                      </div>

                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">Âm thanh</p>
                          <p className="text-sm text-muted-foreground">Phát âm thanh khi có tin nhắn mới</p>
                        </div>
                        <input type="checkbox" className="w-5 h-5" />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 p-6 border-t border-border">
            <Dialog.Close asChild>
              <button className="px-4 py-2 rounded-lg hover:bg-accent">
                Hủy
              </button>
            </Dialog.Close>
            <button className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:opacity-90">
              Lưu thay đổi
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
