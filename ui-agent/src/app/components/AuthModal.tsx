import * as Dialog from "@radix-ui/react-dialog";
import { X, Mail, User, ArrowLeft, Loader2, Sparkles } from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { useAuth } from "../providers/AuthProvider";
import { toast } from "sonner";

interface AuthModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AuthModal({ open, onOpenChange }: AuthModalProps) {
  const { sendOtp, verifyOtp, isGuest } = useAuth();
  
  // Steps: "email" | "otp" | "register"
  const [step, setStep] = useState<"email" | "otp" | "register">("email");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [otp, setOtp] = useState<string[]>(Array(6).fill(""));
  
  const [isLoading, setIsLoading] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [failedAttempts, setFailedAttempts] = useState(0);
  const [formNotice, setFormNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);
  
  const otpInputRefs = useRef<Array<HTMLInputElement | null>>([]);
  const cooldownTimerRef = useRef<NodeJS.Timeout | null>(null);

  const handleSwitchMode = (newMode: "login" | "register") => {
    setMode(newMode);
    setStep("email");
    setOtp(Array(6).fill(""));
    setFailedAttempts(0);
    setFormNotice(null);
  };

  // Focus helper on step change to OTP
  useEffect(() => {
    if (step === "otp") {
      setTimeout(() => {
        otpInputRefs.current[0]?.focus();
      }, 100);
    }
  }, [step]);

  // Handle resend countdown
  useEffect(() => {
    if (cooldown > 0) {
      cooldownTimerRef.current = setTimeout(() => {
        setCooldown((prev) => prev - 1);
      }, 1000);
    }
    return () => {
      if (cooldownTimerRef.current) clearTimeout(cooldownTimerRef.current);
    };
  }, [cooldown]);

  const handleSendOtp = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!email || !email.includes("@")) {
      const message = "Vui lòng nhập địa chỉ email hợp lệ.";
      setFormNotice({ type: "error", text: message });
      toast.error(message);
      return;
    }

    setIsLoading(true);
    setFormNotice(null);
    try {
      await sendOtp(email, mode);
      const message = "Mã OTP đã được gửi đến hòm thư của bạn.";
      setFormNotice({ type: "success", text: message });
      toast.success(message);
      setStep("otp");
      setCooldown(60); // 60s cooldown
      setFailedAttempts(0);
      setOtp(Array(6).fill("")); // Reset OTP
    } catch (err: any) {
      const message = err.message || "Không thể gửi mã OTP.";
      setFormNotice({ type: "error", text: message });
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpInput = (index: number, val: string) => {
    if (val.length > 1) {
      val = val.slice(-1);
    }
    
    // Allow digits only
    if (val && !/^\d$/.test(val)) return;

    const newOtp = [...otp];
    newOtp[index] = val;
    setOtp(newOtp);

    // Auto tab forward
    if (val && index < 5) {
      otpInputRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      // Auto tab backward
      const newOtp = [...otp];
      newOtp[index - 1] = "";
      setOtp(newOtp);
      otpInputRefs.current[index - 1]?.focus();
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    const code = otp.join("");
    if (code.length < 6) {
      toast.error("Vui lòng điền đầy đủ mã xác thực 6 số.");
      return;
    }

    setIsLoading(true);
    try {
      const res = await verifyOtp(email, code);
      if (res.status === "requires_register_name") {
        setStep("register");
      } else {
        // Logged in successfully
        onOpenChange(false);
        resetState();
      }
    } catch (err: any) {
      setFailedAttempts((prev) => prev + 1);
      toast.error(err.message || "Mã xác thực không hợp lệ.");
      
      // Auto clear input to retry
      setOtp(Array(6).fill(""));
      otpInputRefs.current[0]?.focus();
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterName = async (e: React.FormEvent) => {
    e.preventDefault();
    const strippedName = name.trim();
    if (strippedName.length < 2 || strippedName.length > 50) {
      toast.error("Tên hiển thị phải chứa từ 2 đến 50 ký tự.");
      return;
    }

    setIsLoading(true);
    try {
      const code = otp.join("");
      await verifyOtp(email, code, strippedName);
      onOpenChange(false);
      resetState();
    } catch (err: any) {
      toast.error(err.message || "Đăng ký tài khoản thất bại.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    setFormNotice(null);
    try {
      const res = await fetch("/auth/google/url");
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        const message = "Không nhận được cấu hình URL Google OAuth.";
        setFormNotice({ type: "error", text: message });
        toast.error(message);
      }
    } catch (err) {
      console.error(err);
      const message = "Không thể kết nối đến máy chủ xác thực Google.";
      setFormNotice({ type: "error", text: message });
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const resetState = () => {
    setStep("email");
    setMode("login");
    setEmail("");
    setName("");
    setOtp(Array(6).fill(""));
    setFailedAttempts(0);
    setCooldown(0);
    setFormNotice(null);
  };

  return (
    <Dialog.Root open={open} onOpenChange={(o) => {
      onOpenChange(o);
      if (!o) resetState();
    }}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/60 backdrop-blur-md z-[1000] transition-all" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl w-[90vw] max-w-md z-[1001] overflow-hidden text-slate-100 outline-none">
          {/* Subtle glow effect */}
          <div className="absolute -top-40 -left-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-40 -right-40 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />
          
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-slate-800 relative z-10">
            <div className="flex items-center gap-2">
              {step !== "email" && (
                <button 
                  onClick={() => setStep(step === "register" ? "otp" : "email")}
                  className="w-8 h-8 rounded-lg hover:bg-slate-800 flex items-center justify-center text-slate-400 hover:text-slate-200 transition-colors mr-1"
                >
                  <ArrowLeft className="w-4 h-4" />
                </button>
              )}
              <Dialog.Title className="text-xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
                {step === "email" && (mode === "login" ? "Đăng nhập X-Agent" : "Đăng ký X-Agent")}
                {step === "otp" && "Xác nhận OTP"}
                {step === "register" && "Thiết lập hồ sơ"}
              </Dialog.Title>
            </div>
            
            <Dialog.Close asChild>
              <button className="w-8 h-8 rounded-xl hover:bg-slate-800 flex items-center justify-center text-slate-400 hover:text-slate-200 transition-all">
                <X className="w-5 h-5" />
              </button>
            </Dialog.Close>
          </div>

          {/* Form Step: Email */}
          {step === "email" && (
            <div className="p-6 space-y-5 relative z-10">


              <div className="text-center space-y-1">
                <div className="w-12 h-12 bg-blue-500/10 rounded-2xl flex items-center justify-center text-blue-400 mx-auto border border-blue-500/20 mb-2">
                  <Sparkles className="w-6 h-6 animate-pulse" />
                </div>
                <h3 className="text-base font-semibold text-slate-200">
                  {mode === "login" ? "Chào mừng trở lại!" : "Tham gia cùng X-Agent"}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {mode === "login" 
                    ? "Nhập email đã đăng ký của bạn để xác thực OTP đăng nhập."
                    : "Nhập email của bạn để thiết lập tài khoản mới."}
                </p>
              </div>

              <form onSubmit={handleSendOtp} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Địa chỉ Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => {
                        setEmail(e.target.value);
                        setFormNotice(null);
                      }}
                      placeholder="name@company.com"
                      disabled={isLoading}
                      className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-800 bg-slate-950 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all placeholder:text-slate-600 text-sm"
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white font-medium hover:shadow-lg hover:shadow-blue-600/20 transition-all flex items-center justify-center gap-2 cursor-pointer text-sm"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (mode === "login" ? "Tiếp tục đăng nhập" : "Tiếp tục đăng ký")}
                </button>

                {formNotice && (
                  <p
                    className={`text-xs leading-relaxed rounded-xl px-3 py-2 border ${
                      formNotice.type === "error"
                        ? "border-red-500/20 bg-red-500/10 text-red-300"
                        : "border-emerald-500/20 bg-emerald-500/10 text-emerald-300"
                    }`}
                  >
                    {formNotice.text}
                  </p>
                )}
              </form>

              <p className="text-xs text-center text-slate-400 pt-1">
                {mode === "login" ? (
                  <>
                    Chưa có tài khoản?{" "}
                    <button
                      type="button"
                      onClick={() => handleSwitchMode("register")}
                      className="text-blue-400 hover:underline font-semibold cursor-pointer"
                    >
                      Đăng ký ngay
                    </button>
                  </>
                ) : (
                  <>
                    Đã có tài khoản?{" "}
                    <button
                      type="button"
                      onClick={() => handleSwitchMode("login")}
                      className="text-blue-400 hover:underline font-semibold cursor-pointer"
                    >
                      Đăng nhập ngay
                    </button>
                  </>
                )}
              </p>

              <div className="relative flex py-2 items-center">
                <div className="flex-grow border-t border-slate-800"></div>
                <span className="flex-shrink mx-4 text-xs font-semibold uppercase tracking-widest text-slate-600">Hoặc</span>
                <div className="flex-grow border-t border-slate-800"></div>
              </div>

              <div className="space-y-3">
                <button
                  type="button"
                  onClick={handleGoogleLogin}
                  disabled={isLoading}
                  className="w-full py-3 rounded-xl border border-slate-800 hover:bg-slate-800 disabled:opacity-50 text-slate-200 font-medium hover:border-slate-700 transition-all flex items-center justify-center gap-2.5 cursor-pointer text-sm bg-slate-950"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24">
                    <path
                      fill="currentColor"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="currentColor"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="currentColor"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  Tiếp tục với Google
                </button>

                <button
                  type="button"
                  onClick={() => onOpenChange(false)}
                  disabled={isLoading}
                  className="w-full py-3 rounded-xl border border-slate-800/40 hover:bg-slate-850 text-slate-400 hover:text-slate-200 transition-all flex items-center justify-center gap-2 cursor-pointer text-xs"
                >
                  Tiếp tục với chế độ Dùng thử (Guest)
                </button>
              </div>
            </div>
          )}

          {/* Form Step: OTP */}
          {step === "otp" && (
            <div className="p-6 space-y-6 relative z-10">
              <div className="text-center space-y-1">
                <p className="text-xs text-slate-400">Mã OTP xác thực 6 số đã được gửi đến</p>
                <h4 className="text-sm font-semibold text-blue-400 truncate">{email}</h4>
              </div>

              <form onSubmit={handleVerifyOtp} className="space-y-6">
                <div className="flex justify-between gap-2 max-w-[320px] mx-auto">
                  {otp.map((digit, idx) => (
                    <input
                      key={idx}
                      ref={(el) => (otpInputRefs.current[idx] = el)}
                      type="text"
                      inputMode="numeric"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleOtpInput(idx, e.target.value)}
                      onKeyDown={(e) => handleOtpKeyDown(idx, e)}
                      disabled={isLoading || failedAttempts >= 5}
                      className="w-10 h-14 text-center text-xl font-bold bg-slate-950 border border-slate-800 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all"
                    />
                  ))}
                </div>

                {failedAttempts > 0 && (
                  <p className="text-xs text-center text-red-400 font-medium">
                    {failedAttempts >= 5 
                      ? "Mã OTP đã bị khóa. Vui lòng gửi lại mã mới."
                      : `Mã OTP không đúng. Bạn còn ${5 - failedAttempts} lần nhập.`}
                  </p>
                )}

                <button
                  type="submit"
                  disabled={isLoading || failedAttempts >= 5 || otp.join("").length < 6}
                  className="w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800/40 disabled:text-slate-500 text-white font-medium hover:shadow-lg hover:shadow-blue-600/20 transition-all flex items-center justify-center gap-2 cursor-pointer text-sm"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : "Xác nhận mã OTP"}
                </button>
              </form>

              <div className="text-center pt-2">
                {cooldown > 0 ? (
                  <p className="text-xs text-slate-500">
                    Gửi lại mã OTP mới sau <span className="text-blue-400 font-semibold">{cooldown} giây</span>
                  </p>
                ) : (
                  <button
                    type="button"
                    onClick={() => handleSendOtp()}
                    disabled={isLoading}
                    className="text-xs text-blue-400 hover:text-blue-300 font-semibold transition-colors cursor-pointer hover:underline"
                  >
                    Gửi lại mã xác thực mới
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Form Step: Register Name */}
          {step === "register" && (
            <div className="p-6 space-y-5 relative z-10">
              <div className="text-center space-y-1">
                <h3 className="text-base font-semibold text-slate-200">Chào mừng thành viên mới!</h3>
                <p className="text-xs text-slate-400">
                  Hãy thiết lập tên hiển thị của bạn để X-Agent có thể xưng hô thuận tiện nhất.
                </p>
              </div>

              <form onSubmit={handleRegisterName} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Tên hiển thị của bạn</label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                    <input
                      type="text"
                      value={name}
                      onChange={(e) => {
                        setName(e.target.value);
                        setFormNotice(null);
                      }}
                      placeholder="Nguyễn Văn A"
                      disabled={isLoading}
                      className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-800 bg-slate-950 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition-all placeholder:text-slate-600 text-sm"
                      required
                    />
                  </div>
                  <p className="text-[10px] text-slate-500">Tên hiển thị phải chứa từ 2 đến 50 ký tự.</p>
                </div>

                <button
                  type="submit"
                  disabled={isLoading || name.trim().length < 2}
                  className="w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800/40 disabled:text-slate-500 text-white font-medium hover:shadow-lg hover:shadow-blue-600/20 transition-all flex items-center justify-center gap-2 cursor-pointer text-sm"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : "Bắt đầu sử dụng"}
                </button>
              </form>
            </div>
          )}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
