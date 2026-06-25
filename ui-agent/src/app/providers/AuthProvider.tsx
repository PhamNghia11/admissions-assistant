import React, { createContext, useContext, useState, useEffect } from "react";
import { toast } from "sonner";

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  google_id?: string | null;
  provider: "email" | "google";
  created_at: string;
  last_login: string;
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  guestSessionId: string | null;
  isLoading: boolean;
  isGuest: boolean;
  sendOtp: (email: string, action?: "login" | "register") => Promise<void>;
  verifyOtp: (email: string, code: string, name?: string) => Promise<{ status?: string; token?: string; user?: AuthUser }>;
  loginWithGoogle: (code: string, state: string) => Promise<void>;
  updateProfile: (name: string) => Promise<void>;
  deleteAccount: (emailConfirm: string) => Promise<void>;
  logout: () => Promise<void>;
  initializeGuest: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [guestSessionId, setGuestSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize Guest helper
  const initializeGuest = () => {
    let existingGuest = null;
    try {
      existingGuest = localStorage.getItem("guest_session_id");
      if (!existingGuest) {
        existingGuest = `guest_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
        localStorage.setItem("guest_session_id", existingGuest);
        localStorage.setItem("guest_session_created", Date.now().toString());
      } else {
        // Cleanup check for local Guest (24 hours check)
        const createdTime = parseInt(localStorage.getItem("guest_session_created") || "0");
        if (Date.now() - createdTime > 24 * 3600 * 1000) {
          // Expired local Guest
          existingGuest = `guest_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
          localStorage.setItem("guest_session_id", existingGuest);
          localStorage.setItem("guest_session_created", Date.now().toString());
        }
      }
    } catch (e) {
      console.warn("localStorage is not available, using in-memory guest ID.", e);
      existingGuest = `guest_mem_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    }
    setGuestSessionId(existingGuest);
    setToken(null);
    setUser(null);
  };

  useEffect(() => {
    const fetchMe = async () => {
      let storedToken = null;
      try {
        storedToken = localStorage.getItem("auth_token");
      } catch (e) {
        console.warn("Failed to retrieve auth_token from localStorage:", e);
      }

      if (!storedToken) {
        initializeGuest();
        setIsLoading(false);
        return;
      }

      try {
        const res = await fetch("/auth/me", {
          headers: {
            Authorization: `Bearer ${storedToken}`,
          },
        });

        if (res.ok) {
          const userData = await res.json();
          setUser(userData);
          setToken(storedToken);
          try {
            localStorage.removeItem("guest_session_id"); // Clear guest id when logged in
            localStorage.removeItem("guest_session_created");
          } catch (e) {}
          setGuestSessionId(null);
        } else {
          // Token invalid/expired
          try {
            localStorage.removeItem("auth_token");
          } catch (e) {}
          toast.error("Phiên đăng nhập đã hết hạn. Đang chuyển sang chế độ Dùng thử.");
          initializeGuest();
        }
      } catch (err) {
        console.error("Failed to verify authentication:", err);
        initializeGuest();
      } finally {
        setIsLoading(false);
      }
    };

    fetchMe();
  }, []);

  const sendOtp = async (email: string, action?: "login" | "register") => {
    const res = await fetch("/auth/send-otp", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, action }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Không thể gửi mã OTP.");
    }
  };

  const verifyOtp = async (email: string, code: string, name?: string) => {
    const res = await fetch("/auth/verify-otp", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, code, name }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Mã xác thực không hợp lệ.");
    }

    if (data.status === "requires_register_name") {
      return { status: "requires_register_name" };
    }

    if (data.token) {
      localStorage.setItem("auth_token", data.token);
      localStorage.removeItem("guest_session_id"); // Clean guest state
      localStorage.removeItem("guest_session_created");
      setToken(data.token);
      setUser(data.user);
      setGuestSessionId(null);
      if (data.is_new_user) {
        toast.success(`Tài khoản mới đã được tạo! Chào mừng ${data.user.name} đến với X-Agent!`, {
          duration: 5000,
        });
      } else {
        toast.success(`Chào mừng trở lại, ${data.user.name}!`);
      }
    }

    return data;
  };

  const loginWithGoogle = async (code: string, state: string) => {
    const res = await fetch("/auth/google/callback", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ code, state }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Đăng nhập Google thất bại.");
    }

    if (data.token) {
      localStorage.setItem("auth_token", data.token);
      localStorage.removeItem("guest_session_id");
      localStorage.removeItem("guest_session_created");
      setToken(data.token);
      setUser(data.user);
      setGuestSessionId(null);

      if (data.is_new_user) {
        toast.success(`Tài khoản mới đã được tạo! Chào mừng ${data.user.name} đến với X-Agent!`, {
          duration: 5000,
        });
      } else {
        toast.success(`Chào mừng trở lại, ${data.user.name}!`);
      }
    }
  };

  const updateProfile = async (newName: string) => {
    if (!token) return;

    const res = await fetch("/auth/profile", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ name: newName }),
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Không thể cập nhật tên hiển thị.");
    }

    setUser(data);
    toast.success("Đã cập nhật tên hiển thị thành công.");
  };

  const deleteAccount = async (emailConfirm: string) => {
    if (!token || !user) return;

    if (emailConfirm.trim().toLowerCase() !== user.email.toLowerCase()) {
      throw new Error("Địa chỉ email xác nhận không trùng khớp.");
    }

    const res = await fetch("/auth/account", {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Xóa tài khoản thất bại.");
    }

    // Clear FE Auth State
    localStorage.removeItem("auth_token");
    setToken(null);
    setUser(null);
    initializeGuest();
    toast.success("Tài khoản của bạn đã được xóa vĩnh viễn khỏi hệ thống.");
  };

  const logout = async () => {
    try {
      if (token) {
        await fetch("/auth/logout", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
      }
    } catch (err) {
      console.warn("Server-side logout warning:", err);
    }

    localStorage.removeItem("auth_token");
    setToken(null);
    setUser(null);
    initializeGuest();
    toast.success("Đã đăng xuất. Bạn đang ở chế độ Dùng thử (Guest).");
  };

  const isGuest = user === null;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        guestSessionId,
        isLoading,
        isGuest,
        sendOtp,
        verifyOtp,
        loginWithGoogle,
        updateProfile,
        deleteAccount,
        logout,
        initializeGuest,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
