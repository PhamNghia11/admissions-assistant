import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <button className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-accent transition-colors">
        <Sun className="w-4 h-4" />
        <span>Chế độ sáng</span>
      </button>
    );
  }

  return (
    <button
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      className="flex items-center gap-2 px-4 py-2 rounded-lg hover:bg-accent transition-colors w-full"
    >
      {theme === "dark" ? (
        <>
          <Sun className="w-4 h-4" />
          <span>Chế độ sáng</span>
        </>
      ) : (
        <>
          <Moon className="w-4 h-4" />
          <span>Chế độ tối</span>
        </>
      )}
    </button>
  );
}
