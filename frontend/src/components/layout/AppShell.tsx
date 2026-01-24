import { ReactNode, useEffect } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { useUIStore } from "@/stores/uiStore";
import { cn } from "@/lib/utils";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const { sidebarOpen, sidebarCollapsed, setIsMobile } = useUIStore();

  // Handle responsive behavior
  useEffect(() => {
    const handleResize = () => {
      const isMobile = window.innerWidth < 768;
      setIsMobile(isMobile);
    };

    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [setIsMobile]);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content area */}
      <div
        className={cn(
          "flex flex-1 flex-col overflow-hidden transition-all duration-200",
          sidebarOpen && !sidebarCollapsed && "md:ml-64",
          sidebarOpen && sidebarCollapsed && "md:ml-16"
        )}
      >
        {/* Header */}
        <Header />

        {/* Page content */}
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
