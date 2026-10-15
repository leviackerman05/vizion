
import { Moon, Sun } from "lucide-react";
import { useTheme } from "./theme-provider";
import { Button } from "@/components/ui/button";
import { Toggle } from "@/components/ui/toggle";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <Toggle
      aria-label="Toggle theme"
      pressed={theme === "dark"}
      onPressedChange={(pressed) => setTheme(pressed ? "dark" : "light")}
      variant="outline"
      size="sm"
    >
      {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
    </Toggle>
  );
}
