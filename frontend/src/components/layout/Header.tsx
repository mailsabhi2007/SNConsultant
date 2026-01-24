import { Menu, Plus, LogOut, Settings, Shield } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Avatar } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ThemeToggle } from "./ThemeToggle";
import { useUIStore } from "@/stores/uiStore";
import { useAuthStore } from "@/store/authStore";
import { useChat } from "@/hooks/useChat";
import { logout } from "@/services/auth";
import { ROUTES } from "@/lib/constants";

export function Header() {
  const navigate = useNavigate();
  const { toggleSidebar, isMobile } = useUIStore();
  const { user, setUser } = useAuthStore();
  const { newConversation } = useChat();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (e) {
      // Ignore errors
    }
    setUser(null);
    navigate(ROUTES.LOGIN);
  };

  const handleNewChat = () => {
    newConversation();
    navigate(ROUTES.CHAT);
  };

  return (
    <header className="flex h-14 items-center justify-between border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex items-center gap-2">
        {/* Mobile menu toggle */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={toggleSidebar}
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Sidebar toggle for desktop */}
        <Button
          variant="ghost"
          size="icon"
          className="hidden md:flex"
          onClick={toggleSidebar}
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* New chat button */}
        <Button
          variant="outline"
          size="sm"
          className="gap-2"
          onClick={handleNewChat}
        >
          <Plus className="h-4 w-4" />
          <span className="hidden sm:inline">New Chat</span>
        </Button>
      </div>

      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <ThemeToggle />

        {/* User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-9 w-9 rounded-full">
              <Avatar
                fallback={user?.username?.charAt(0).toUpperCase() || "U"}
                className="h-9 w-9"
              />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">
                  {user?.username || "User"}
                </p>
                <p className="text-xs leading-none text-muted-foreground">
                  {user?.is_admin ? "Administrator" : "User"}
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate(ROUTES.SETTINGS)}>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            {user?.is_admin && (
              <DropdownMenuItem onClick={() => navigate(ROUTES.ADMIN)}>
                <Shield className="mr-2 h-4 w-4" />
                Admin Console
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={handleLogout}
              className="text-destructive focus:text-destructive"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
