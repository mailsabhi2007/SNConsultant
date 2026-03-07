import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import {
  MessageSquare,
  BookOpen,
  Settings,
  ShieldCheck,
  Brain,
  ChevronLeft,
  ChevronRight,
  Plus,
  X,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ConversationList } from "@/components/conversation/ConversationList";
import { useUIStore } from "@/stores/uiStore";
import { useAuthStore } from "@/store/authStore";
import { useCreditStore } from "@/stores/creditStore";
import { cn } from "@/lib/utils";
import { ROUTES, APP_NAME } from "@/lib/constants";
import { getBalance } from "@/services/credits";

const navItems = [
  { icon: MessageSquare, label: "Chat", path: ROUTES.CHAT },
  { icon: BookOpen, label: "Knowledge Base", path: ROUTES.KNOWLEDGE_BASE },
  { icon: Settings, label: "Settings", path: ROUTES.SETTINGS },
];

export function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuthStore();
  const { balance, setBalance } = useCreditStore();
  const {
    sidebarOpen,
    sidebarCollapsed,
    isMobile,
    setSidebarOpen,
    setSidebarCollapsed,
  } = useUIStore();

  // Poll credit balance on mount and every 60s
  useEffect(() => {
    if (!user) return;
    const fetchBalance = () => getBalance().then((b) => setBalance(b.balance)).catch(() => {});
    fetchBalance();
    const interval = setInterval(fetchBalance, 60_000);
    return () => clearInterval(interval);
  }, [user, setBalance]);

  useEffect(() => {
    if (isMobile) setSidebarOpen(false);
  }, [location.pathname, isMobile, setSidebarOpen]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isMobile && sidebarOpen) setSidebarOpen(false);
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, [isMobile, sidebarOpen, setSidebarOpen]);

  const isActive = (path: string) => location.pathname === path;

  const handleNavigate = (path: string) => {
    navigate(path);
    if (isMobile) setSidebarOpen(false);
  };

  const collapsed = sidebarCollapsed && !isMobile;

  const sidebarContent = (
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex items-center gap-3 px-4 py-5 border-b border-white/[0.06]">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary shadow-lg shadow-primary/10">
            <Brain className="h-5 w-5" />
          </div>
          {!collapsed && (
            <span className="text-lg font-bold tracking-tight text-sidebar-foreground">
              {APP_NAME}
            </span>
          )}
          {isMobile && (
            <Button
              variant="ghost"
              size="icon"
              className="ml-auto h-8 w-8 text-muted-foreground"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex flex-col gap-1 px-2 py-3">
          {navItems.map((item) => {
            const active = isActive(item.path);
            return (
              <button
                key={item.path}
                onClick={() => handleNavigate(item.path)}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors w-full text-left",
                  active
                    ? "bg-white/[0.08] text-sidebar-primary backdrop-blur-sm shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)]"
                    : "text-sidebar-foreground/70 hover:bg-white/[0.04] hover:text-sidebar-foreground",
                  collapsed && "justify-center px-2"
                )}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </button>
            );
          })}

          {user?.is_admin && (
            <button
              onClick={() => handleNavigate(ROUTES.ADMIN)}
              title={collapsed ? "Admin" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors w-full text-left",
                isActive(ROUTES.ADMIN)
                  ? "bg-white/[0.08] text-sidebar-primary backdrop-blur-sm shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)]"
                  : "text-sidebar-foreground/70 hover:bg-white/[0.04] hover:text-sidebar-foreground",
                collapsed && "justify-center px-2"
              )}
            >
              <ShieldCheck className="h-4 w-4 shrink-0" />
              {!collapsed && <span>Admin</span>}
            </button>
          )}
        </nav>

        {/* Divider */}
        <div className="mx-4 border-t border-white/[0.06]" />

        {/* Recent Conversations */}
        {!collapsed && (
          <div className="flex flex-1 flex-col overflow-hidden px-2 py-3">
            <div className="flex items-center justify-between px-3 pb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Recent Conversations
              </span>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 text-muted-foreground hover:text-foreground"
                onClick={() => handleNavigate(ROUTES.CHAT)}
              >
                <Plus className="h-3.5 w-3.5" />
                <span className="sr-only">New conversation</span>
              </Button>
            </div>
            <ScrollArea className="flex-1">
              <ConversationList />
            </ScrollArea>
          </div>
        )}

        {/* Credit balance badge */}
        {balance !== null && (
          <div className={cn(
            "mx-2 mb-1 rounded-lg px-3 py-2 border border-white/[0.06]",
            balance === 0
              ? "bg-destructive/10 border-destructive/20"
              : balance < 50
              ? "bg-yellow-500/10 border-yellow-500/20"
              : "bg-white/[0.03]",
            collapsed && "px-2 flex justify-center"
          )}>
            {collapsed ? (
              <Zap className={cn("h-4 w-4", balance === 0 ? "text-destructive" : balance < 50 ? "text-yellow-400" : "text-primary")} />
            ) : (
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5">
                  <Zap className={cn("h-3.5 w-3.5 shrink-0", balance === 0 ? "text-destructive" : balance < 50 ? "text-yellow-400" : "text-primary")} />
                  <span className={cn("text-xs font-semibold tabular-nums", balance === 0 ? "text-destructive" : balance < 50 ? "text-yellow-400" : "text-foreground")}>
                    {balance.toLocaleString()}
                  </span>
                </div>
                <span className="text-[10px] text-muted-foreground/60">credits</span>
              </div>
            )}
          </div>
        )}

        {/* Collapse toggle (desktop only) */}
        {!isMobile && (
          <div className="border-t border-white/[0.06] p-2">
            <Button
              variant="ghost"
              size="icon"
              className="w-full text-muted-foreground hover:text-foreground"
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            >
              {collapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
              <span className="sr-only">{collapsed ? "Expand sidebar" : "Collapse sidebar"}</span>
            </Button>
          </div>
        )}
      </div>
  );

  // Mobile overlay
  if (isMobile) {
    return (
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
              onClick={() => setSidebarOpen(false)}
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed inset-y-0 left-0 z-50 w-[280px] bg-sidebar/95 backdrop-blur-2xl border-r border-white/[0.06]"
            >
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    );
  }

  if (!sidebarOpen) return null;

  return (
    <aside
      className={cn(
        "hidden border-r border-white/[0.06] bg-sidebar/80 backdrop-blur-2xl transition-all duration-300 md:flex flex-col h-full",
        collapsed ? "w-16" : "w-[280px]"
      )}
    >
      {sidebarContent}
    </aside>
  );
}
