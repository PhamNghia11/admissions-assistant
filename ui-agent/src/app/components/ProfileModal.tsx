import * as Dialog from "@radix-ui/react-dialog";
import { X, Mail, User as UserIcon, Calendar, Shield, Loader2, Trash2, Edit2, Check } from "lucide-react";
import { useState, useEffect } from "react";
import { useAuth } from "../providers/AuthProvider";
import { toast } from "sonner";

interface ProfileModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ProfileModal({ open, onOpenChange }: ProfileModalProps) {
  const { user, updateProfile, deleteAccount } = useAuth();
  
  const [name, setName] = useState("");
  const [isEditingName, setIsEditingName] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Account Deletion Confirmation States
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [emailConfirmInput, setEmailConfirmInput] = useState("");

  // Initialize input when modal opens or user state updates
  useEffect(() => {
    if (user) {
      setName(user.name);
    }
  }, [user, open]);

  if (!user) return null;

  const handleUpdateName = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = name.trim();
    
    if (trimmed === user.name) {
      setIsEditingName(false);
      return;
    }

    if (trimmed.length < 2 || trimmed.length > 50) {
      toast.error("Tên hiển thị phải chứa từ 2 đến 50 ký tự.");
      return;
    }

    setIsLoading(true);
    try {
      await updateProfile(trimmed);
      setIsEditingName(false);
    } catch (err: any) {
      toast.error(err.message || "Không thể cập nhật tên hiển thị.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    if (emailConfirmInput.trim().toLowerCase() !== user.email.toLowerCase()) {
      toast.error("Địa chỉ email xác thực không trùng khớp.");
      return;
    }

    setIsLoading(true);
    try {
      await deleteAccount(emailConfirmInput.trim());
      onOpenChange(false);
      resetState();
    } catch (err: any) {
      toast.error(err.message || "Xóa tài khoản thất bại.");
    } finally {
      setIsLoading(false);
    }
  };

  const resetState = () => {
    setIsEditingName(false);
    setShowDeleteConfirm(false);
    setEmailConfirmInput("");
  };

  const formatDate = (isoStr: string) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString("vi-VN", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit"
      });
    } catch (e) {
      return isoStr;
    }
  };

  // Generate beautiful gradient avatar
  const getGradientAvatar = (nameStr: string) => {
    const char = nameStr.charAt(0).toUpperCase();
    return (
      <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 flex items-center justify-center text-white text-4xl font-extrabold shadow-lg shadow-indigo-500/20 ring-4 ring-slate-800">
        {char}
      </div>
    );
  };

  return (
    <Dialog.Root open={open} onOpenChange={(o) => {
      onOpenChange(o);
      if (!o) resetState();
    }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-md z-[1000] transition-all" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl w-[90vw] max-w-md z-[1001] overflow-hidden text-slate-100 outline-none">
          
          {/* Decorative gradients */}
          <div className="absolute -top-40 -left-40 w-80 h-80 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-40 -right-40 w-80 h-80 bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />

          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-slate-800 relative z-10">
            <Dialog.Title className="text-xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
              {showDeleteConfirm ? "Xác nhận xóa tài khoản" : "Hồ sơ cá nhân"}
            </Dialog.Title>
            <Dialog.Close asChild>
              <button className="w-8 h-8 rounded-xl hover:bg-slate-800 flex items-center justify-center text-slate-400 hover:text-slate-200 transition-all">
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>

          {/* Main Content */}
          {!showDeleteConfirm ? (
            <div className="p-6 space-y-6 relative z-10">
              {/* Profile Card & Avatar */}
              <div className="flex flex-col items-center text-center space-y-3">
                {user.avatar_url ? (
                  <img 
                    src={user.avatar_url} 
                    alt={user.name} 
                    className="w-24 h-24 rounded-3xl object-cover shadow-lg ring-4 ring-slate-800 shadow-slate-950/40"
                  />
                ) : (
                  getGradientAvatar(user.name)
                )}
                
                <div className="space-y-1.5 w-full">
                  {isEditingName ? (
                    <form onSubmit={handleUpdateName} className="flex items-center gap-2 max-w-[280px] mx-auto pt-1">
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        disabled={isLoading}
                        className="flex-grow px-3 py-1.5 rounded-lg border border-slate-800 bg-slate-950 text-slate-100 focus:border-blue-500 outline-none text-sm font-semibold"
                        required
                        autoFocus
                      />
                      <button
                        type="submit"
                        disabled={isLoading}
                        className="w-8 h-8 rounded-lg bg-blue-600 hover:bg-blue-500 flex items-center justify-center text-white cursor-pointer hover:shadow-md transition-all shrink-0"
                      >
                        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                      </button>
                    </form>
                  ) : (
                    <div className="flex items-center justify-center gap-2 group">
                      <h3 className="text-xl font-bold text-slate-100 tracking-tight">{user.name}</h3>
                      <button 
                        onClick={() => setIsEditingName(true)}
                        className="text-slate-500 hover:text-slate-300 p-1 rounded-lg transition-colors cursor-pointer"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}

                  <p className="text-xs text-slate-400 font-medium flex items-center justify-center gap-1.5">
                    <Mail className="w-3.5 h-3.5 text-slate-500" /> {user.email}
                  </p>
                </div>
              </div>

              {/* Stats & Meta info */}
              <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4 space-y-3.5">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center gap-2"><Shield className="w-4 h-4 text-slate-500" /> Phương thức</span>
                  <span className="font-semibold text-slate-200 capitalize bg-slate-900 border border-slate-800 px-2 py-0.5 rounded-md">
                    {user.provider === "google"
                      ? "Google OAuth"
                      : user.google_id
                        ? "Email OTP + Google"
                        : "Email OTP"}
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center gap-2"><Calendar className="w-4 h-4 text-slate-500" /> Ngày tham gia</span>
                  <span className="font-semibold text-slate-200">
                    {formatDate(user.created_at)}
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span className="flex items-center gap-2"><Calendar className="w-4 h-4 text-slate-500" /> Đăng nhập cuối</span>
                  <span className="font-semibold text-slate-200">
                    {formatDate(user.last_login)}
                  </span>
                </div>
              </div>

              {/* Danger Zone */}
              <div className="pt-2 border-t border-slate-800 flex justify-between items-center">
                <button
                  type="button"
                  onClick={() => setShowDeleteConfirm(true)}
                  className="flex items-center gap-2 text-xs font-semibold text-red-500 hover:text-red-400 transition-colors py-2 cursor-pointer group"
                >
                  <Trash2 className="w-4 h-4 group-hover:scale-105 transition-transform" /> Xóa vĩnh viễn tài khoản
                </button>
              </div>
            </div>
          ) : (
            /* Step 2: Delete Account Confirmation */
            <div className="p-6 space-y-5 relative z-10">
              <div className="rounded-2xl border border-red-500/10 bg-red-950/20 p-4 space-y-2">
                <h4 className="text-sm font-bold text-red-400">⚠️ Lưu ý cực kỳ quan trọng!</h4>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Hành động này <span className="font-bold text-red-400">KHÔNG THỂ hoàn tác</span>. Toàn bộ dữ liệu tài khoản, lịch sử hội thoại, các tệp tài liệu đã tải lên X-Agent của bạn sẽ bị xóa vĩnh viễn khỏi máy chủ.
                </p>
              </div>

              <form onSubmit={handleDeleteAccount} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-400 leading-relaxed block">
                    Để xác nhận, vui lòng nhập chính xác địa chỉ email của bạn:
                    <span className="text-blue-400 block font-bold mt-1 select-all">{user.email}</span>
                  </label>
                  
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                    <input
                      type="email"
                      value={emailConfirmInput}
                      onChange={(e) => setEmailConfirmInput(e.target.value)}
                      placeholder={user.email}
                      disabled={isLoading}
                      className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-800 bg-slate-950 focus:border-red-500 focus:ring-2 focus:ring-red-500/20 outline-none transition-all placeholder:text-slate-700 text-sm"
                      required
                    />
                  </div>
                </div>

                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setShowDeleteConfirm(false);
                      setEmailConfirmInput("");
                    }}
                    disabled={isLoading}
                    className="flex-1 py-3 rounded-xl border border-slate-800 hover:bg-slate-800 disabled:opacity-50 text-slate-300 font-medium transition-all cursor-pointer text-xs"
                  >
                    Hủy bỏ
                  </button>

                  <button
                    type="submit"
                    disabled={isLoading || emailConfirmInput.trim().toLowerCase() !== user.email.toLowerCase()}
                    className="flex-1 py-3 rounded-xl bg-red-600 hover:bg-red-500 disabled:bg-red-800/40 disabled:text-slate-500 text-white font-medium hover:shadow-lg hover:shadow-red-600/20 transition-all flex items-center justify-center gap-2 cursor-pointer text-xs"
                  >
                    {isLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : "Xác nhận xóa"}
                  </button>
                </div>
              </form>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
