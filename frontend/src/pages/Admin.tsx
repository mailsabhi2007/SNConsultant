import { useEffect, useState } from "react";
import { Loader2, Database, FolderOpen, Users, MessageSquare, Zap, FileText } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getAdminStats, AdminStats } from "@/services/admin";

interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon: React.ReactNode;
}

function StatCard({ title, value, description, icon }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

export function AdminPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAdminStats()
      .then(setStats)
      .catch((err) => {
        setError("Failed to load admin statistics");
        setStats(null);
      })
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-8">
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">
              {error || "No statistics available or you are not authorized to view this page."}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Extract stats from the response
  const dbStats = stats.database as Record<string, number> || {};
  const kbStats = stats.knowledge_base as Record<string, number> || {};

  return (
    <div className="container mx-auto max-w-6xl px-4 py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Admin Console</h1>
          <p className="mt-1 text-muted-foreground">
            System statistics and administration tools.
          </p>
        </div>
        <Badge variant="secondary">Admin</Badge>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mb-8">
        <StatCard
          title="Total Users"
          value={dbStats.total_users || 0}
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          title="Total Conversations"
          value={dbStats.total_conversations || 0}
          icon={<MessageSquare className="h-4 w-4" />}
        />
        <StatCard
          title="Total Messages"
          value={dbStats.total_messages || 0}
          icon={<Zap className="h-4 w-4" />}
        />
        <StatCard
          title="Knowledge Base Files"
          value={kbStats.total_documents || 0}
          icon={<FileText className="h-4 w-4" />}
        />
        <StatCard
          title="Total Chunks"
          value={kbStats.total_chunks || 0}
          description="Indexed document chunks"
          icon={<FolderOpen className="h-4 w-4" />}
        />
        <StatCard
          title="Database Size"
          value={formatBytes(dbStats.db_size_bytes || 0)}
          icon={<Database className="h-4 w-4" />}
        />
      </div>

      {/* Detailed Stats */}
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Database Statistics</CardTitle>
            <CardDescription>Core database metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(dbStats).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">
                    {formatStatKey(key)}
                  </span>
                  <span className="font-medium">
                    {typeof value === "number" && key.includes("bytes")
                      ? formatBytes(value)
                      : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Knowledge Base Statistics</CardTitle>
            <CardDescription>Vector store metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(kbStats).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">
                    {formatStatKey(key)}
                  </span>
                  <span className="font-medium">
                    {typeof value === "number" && key.includes("bytes")
                      ? formatBytes(value)
                      : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function formatStatKey(key: string): string {
  return key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}
