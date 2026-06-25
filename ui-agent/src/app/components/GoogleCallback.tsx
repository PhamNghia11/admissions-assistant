import { useEffect, useRef, useState } from "react";
import { useAuth } from "../providers/AuthProvider";
import { toast } from "sonner";
import { Loader2, ArrowLeft } from "lucide-react";

export function GoogleCallback() {
  const { loginWithGoogle } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const handledRef = useRef(false);

  useEffect(() => {
    if (handledRef.current) {
      return;
    }
    handledRef.current = true;

    const handleCallback = async () => {
      const params = new URLSearchParams(window.location.search);
      const code = params.get("code");
      const state = params.get("state");

      if (!code || !state) {
        setError("Thiếu tham số xác thực từ Google.");
        toast.error("Đăng nhập thất bại: Thiếu code hoặc state.");
        return;
      }

      try {
        await loginWithGoogle(code, state);
        // Successful Google login: replace the callback URL so the page cannot be replayed.
        window.location.replace("/");
      } catch (err: any) {
        console.error("Google Auth error:", err);
        setError(err.message || "Đăng nhập Google thất bại.");
        toast.error(err.message || "Đăng nhập bằng Google thất bại.");
      }
    };

    handleCallback();
  }, [loginWithGoogle]);

  return (
    <div className="fixed inset-0 bg-[#0f172a] flex flex-col items-center justify-center z-[9999] px-6 text-center">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(59,130,246,0.08),transparent_70%)] pointer-events-none" />
      
      <div className="max-w-md w-full p-8 rounded-3xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl shadow-2xl relative z-10 flex flex-col items-center">
        <div className="text-3xl font-extrabold bg-gradient-to-br from-blue-400 to-purple-500 bg-clip-text text-transparent mb-6 tracking-tight">
          X-Agent Auth
        </div>

        {error ? (
          <div className="space-y-4">
            <div className="w-16 h-16 rounded-full bg-red-950/50 border border-red-500/30 flex items-center justify-center text-red-500 text-3xl font-bold mx-auto mb-4">
              !
            </div>
            <h2 className="text-xl font-bold text-slate-100">Đã xảy ra lỗi</h2>
            <p className="text-sm text-slate-400 leading-relaxed">{error}</p>
            <p className="text-xs text-slate-500 pt-4">Bạn có thể quay lại trang đăng nhập để thử lại.</p>
            <button
              type="button"
              onClick={() => {
                window.location.replace("/");
              }}
              className="mt-2 inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-900 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Quay lại đăng nhập
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="relative flex items-center justify-center w-20 h-20">
              {/* Spinning glow ring */}
              <div className="absolute inset-0 rounded-full border-t-2 border-r-2 border-blue-500 animate-spin" />
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
            </div>
            
            <div className="space-y-2">
              <h2 className="text-xl font-bold text-slate-100 tracking-wide">Đang liên kết tài khoản</h2>
              <p className="text-sm text-slate-400 leading-relaxed">
                Đang xác thực thông tin tài khoản Google của bạn với máy chủ bảo mật X-Agent...
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
