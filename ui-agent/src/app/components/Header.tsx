import { LogIn, User, LogOut, Settings, Shield } from "lucide-react";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";
import { useAuth } from "../providers/AuthProvider";

interface HeaderProps {
  onAuthClick: () => void;
  onProfileClick: () => void;
  onSettingsClick: () => void;
}

export function Header({ onAuthClick, onProfileClick, onSettingsClick }: HeaderProps) {
  const { user, logout } = useAuth();

  return (
    <div className="h-14 border-b border-border bg-background flex items-center justify-end px-6 gap-3">
      {/* Auth Section */}
      {user ? (
        <DropdownMenu.Root>
          <DropdownMenu.Trigger asChild>
            <button className="flex items-center gap-3 px-2 py-1.5 rounded-xl hover:bg-accent transition-all outline-none border border-transparent hover:border-slate-800 cursor-pointer">
              {user.avatar_url ? (
                <img 
                  src={user.avatar_url} 
                  alt={user.name} 
                  className="w-9 h-9 rounded-xl object-cover ring-2 ring-slate-800"
                />
              ) : (
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-sm shadow-md ring-2 ring-slate-800">
                  {user.name.charAt(0).toUpperCase()}
                </div>
              )}
              <div className="text-left hidden md:block">
                <p className="text-sm font-semibold text-slate-200">{user.name}</p>
                <p className="text-xs text-slate-500 truncate max-w-[120px]">{user.email}</p>
              </div>
            </button>
          </DropdownMenu.Trigger>

          <DropdownMenu.Portal>
            <DropdownMenu.Content
              className="bg-popover border border-border rounded-2xl shadow-2xl p-2 min-w-[240px] z-[999] outline-none relative overflow-hidden"
              sideOffset={6}
              align="end"
            >
              {/* Subtle backdrop glow */}
              <div className="absolute -top-12 -right-12 w-24 h-24 bg-blue-500/5 rounded-full blur-xl pointer-events-none" />
              
              <div className="px-3 py-3 border-b border-border mb-1.5 relative z-10">
                <div className="flex items-center gap-3">
                  {user.avatar_url ? (
                    <img 
                      src={user.avatar_url} 
                      alt={user.name} 
                      className="w-11 h-11 rounded-xl object-cover"
                    />
                  ) : (
                    <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-base shadow-inner">
                      {user.name.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-slate-200 truncate">{user.name}</p>
                    <p className="text-xs text-slate-500 truncate">{user.email}</p>
                  </div>
                </div>
              </div>

              <DropdownMenu.Item
                className="px-3 py-2 rounded-lg hover:bg-slate-800 cursor-pointer outline-none flex items-center gap-3 text-slate-300 transition-colors hover:text-slate-100 text-sm"
                onSelect={onProfileClick}
              >
                <User className="w-4 h-4 text-slate-500" />
                <span>Hồ sơ của tôi</span>
              </DropdownMenu.Item>

              <DropdownMenu.Item
                className="px-3 py-2 rounded-lg hover:bg-slate-800 cursor-pointer outline-none flex items-center gap-3 text-slate-300 transition-colors hover:text-slate-100 text-sm"
                onSelect={onSettingsClick}
              >
                <Settings className="w-4 h-4 text-slate-500" />
                <span>Cài đặt hệ thống</span>
              </DropdownMenu.Item>

              <div className="h-[1px] bg-border my-1" />

              <DropdownMenu.Item
                className="px-3 py-2 rounded-lg hover:bg-red-950/40 cursor-pointer outline-none flex items-center gap-3 text-red-400 transition-colors hover:text-red-300 text-sm"
                onSelect={() => logout()}
              >
                <LogOut className="w-4 h-4" />
                <span>Đăng xuất</span>
              </DropdownMenu.Item>
            </DropdownMenu.Content>
          </DropdownMenu.Portal>
        </DropdownMenu.Root>
      ) : (
        <button
          onClick={onAuthClick}
          className="flex items-center gap-2 px-4 py-2 rounded-xl border border-blue-500/30 hover:border-blue-500/50 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 hover:text-blue-300 font-semibold transition-all cursor-pointer text-sm hover:shadow-lg hover:shadow-blue-500/5"
        >
          <LogIn className="w-4 h-4 animate-pulse" />
          <span>Đăng nhập</span>
        </button>
      )}
    </div>
  );
}
