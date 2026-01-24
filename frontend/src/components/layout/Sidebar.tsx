import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  MessageSquare,
  FolderOpen,
  Settings,
  Shield,
  ChevronLeft,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ConversationList } from "@/components/conversation/ConversationList";
import { useUIStore } from "@/stores/uiStore";
import { useAuthStore } from "@/store/authStore";
import { cn } from "@/lib/utils";
import { ROUTES, APP_NAME } from "@/lib/constants";

const navItems = [
  { icon: MessageSquare, label: "Chat", path: ROUTES.CHAT },
  { icon: FolderOpen, label: "Knowledge Base", path: ROUTES.KNOWLEDGE_BASE },
  { icon: Settings, label: "Settings", path: ROUTES.SETTINGS },
];

export function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuthStore();
  const {
    sidebarOpen,
    sidebarCollapsed,
    isMobile,
    setSidebarOpen,
    setSidebarCollapsed,
  } = useUIStore();

  // Close sidebar on mobile when navigating
  useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  }, [location.pathname, isMobile, setSidebarOpen]);

  // Handle escape key to close sidebar on mobile
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isMobile && sidebarOpen) {
        setSidebarOpen(false);
      }
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isMobile, sidebarOpen, setSidebarOpen]);

  const isActive = (path: string) => location.pathname === path;

  const handleNavigate = (path: string) => {
    navigate(path);
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  const sidebarContent = (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex h-14 items-center justify-between border-b px-4">
        {!sidebarCollapsed && (
          <h1 className="text-lg font-semibold tracking-tight">{APP_NAME}</h1>
        )}
        {isMobile ? (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        ) : (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className={cn(sidebarCollapsed && "mx-auto")}
          >
            <ChevronLeft
              className={cn(
                "h-5 w-5 transition-transform",
                sidebarCollapsed && "rotate-180"
              )}
            />
          </Button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-1 p-2">
        {navItems.map((item) => (
          <Button
            key={item.path}
            variant={isActive(item.path) ? "secondary" : "ghost"}
            className={cn(
              "justify-start gap-3",
              sidebarCollapsed && "justify-center px-2"
            )}
            onClick={() => handleNavigate(item.path)}
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {!sidebarCollapsed && <span>{item.label}</span>}
          </Button>
        ))}

        {user?.is_admin && (
          <Button
            variant={isActive(ROUTES.ADMIN) ? "secondary" : "ghost"}
            className={cn(
              "justify-start gap-3",
              sidebarCollapsed && "justify-center px-2"
            )}
            onClick={() => handleNavigate(ROUTES.ADMIN)}
          >
            <Shield className="h-4 w-4 shrink-0" />
            {!sidebarCollapsed && <span>Admin</span>}
          </Button>
        )}
      </nav>

      {/* Conversations */}
      {!sidebarCollapsed && (
        <div className="flex-1 overflow-hidden border-t">
          <div className="px-4 py-2">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Recent Chats
            </h2>
          </div>
          <ScrollArea className="h-[calc(100%-36px)]">
            <ConversationList />
          </ScrollArea>
        </div>
      )}
    </div>
  );

  // Mobile overlay sidebar
  if (isMobile) {
    return (
      <AnimatePresence>
        {sidebarOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/50"
              onClick={() => setSidebarOpen(false)}
            />

            {/* Sidebar */}
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed inset-y-0 left-0 z-50 w-64 bg-background shadow-xl"
            >
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    );
  }

  // Desktop fixed sidebar
  if (!sidebarOpen) return null;

  return (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-30 hidden border-r bg-background transition-all duration-200 md:block",
        sidebarCollapsed ? "w-16" : "w-64"
      )}
    >
      {sidebarContent}
    </aside>
  );
}
