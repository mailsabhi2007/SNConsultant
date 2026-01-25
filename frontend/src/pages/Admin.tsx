import { useEffect, useState } from "react";
import {
  Loader2,
  Users,
  MessageSquare,
  Activity,
  Clock,
  TrendingUp,
  UserPlus,
  Calendar,
  Mail,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  getSystemAnalytics,
  getAllUsersAnalytics,
  getUserSessions,
  getUserPrompts,
  SystemAnalytics,
  UserAnalytics,
  UserSession,
  UserPrompt,
} from "@/services/admin";

interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon: React.ReactNode;
  trend?: string;
}

function StatCard({ title, value, description, icon, trend }: StatCardProps) {
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
        {trend && (
          <div className="flex items-center gap-1 mt-2 text-xs text-green-600">
            <TrendingUp className="h-3 w-3" />
            {trend}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function AdminPage() {
  const [analytics, setAnalytics] = useState<SystemAnalytics | null>(null);
  const [users, setUsers] = useState<UserAnalytics[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUser, setSelectedUser] = useState<UserAnalytics | null>(null);
  const [userSessions, setUserSessions] = useState<UserSession[]>([]);
  const [userPrompts, setUserPrompts] = useState<UserPrompt[]>([]);
  const [loadingUserDetails, setLoadingUserDetails] = useState(false);
  const [sortBy, setSortBy] = useState<keyof UserAnalytics>("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    Promise.all([getSystemAnalytics(), getAllUsersAnalytics()])
      .then(([analyticsData, usersData]) => {
        setAnalytics(analyticsData);
        setUsers(usersData);
      })
      .catch(() => {
        setError("Failed to load admin analytics");
      })
      .finally(() => setIsLoading(false));
  }, []);

  const handleUserClick = async (user: UserAnalytics) => {
    setSelectedUser(user);
    setLoadingUserDetails(true);
    try {
      const [sessions, prompts] = await Promise.all([
        getUserSessions(user.user_id),
        getUserPrompts(user.user_id),
      ]);
      setUserSessions(sessions);
      setUserPrompts(prompts);
    } catch (err) {
      console.error("Failed to load user details:", err);
    } finally {
      setLoadingUserDetails(false);
    }
  };

  const handleSort = (column: keyof UserAnalytics) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(column);
      setSortOrder("desc");
    }
  };

  const sortedUsers = [...users].sort((a, b) => {
    const aVal = a[sortBy];
    const bVal = b[sortBy];

    if (aVal === null) return 1;
    if (bVal === null) return -1;

    if (typeof aVal === "string" && typeof bVal === "string") {
      return sortOrder === "asc" ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    }

    if (typeof aVal === "number" && typeof bVal === "number") {
      return sortOrder === "asc" ? aVal - bVal : bVal - aVal;
    }

    return 0;
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="container mx-auto max-w-4xl px-4 py-8">
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">
              {error || "No analytics available or you are not authorized to view this page."}
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const formatDuration = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  };

  const formatDate = (dateString: string | null): string => {
    if (!dateString) return "Never";
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const formatDateTime = (dateString: string | null): string => {
    if (!dateString) return "Never";
    return new Date(dateString).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const SortIcon = ({ column }: { column: keyof UserAnalytics }) => {
    if (sortBy !== column) return null;
    return sortOrder === "asc" ? (
      <ChevronUp className="h-4 w-4 inline ml-1" />
    ) : (
      <ChevronDown className="h-4 w-4 inline ml-1" />
    );
  };

  return (
    <div className="container mx-auto max-w-7xl px-4 py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Admin Dashboard</h1>
          <p className="mt-1 text-muted-foreground">
            User analytics and system monitoring
          </p>
        </div>
        <Badge variant="secondary">Admin</Badge>
      </div>

      {/* Analytics Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
        <StatCard
          title="Total Users"
          value={analytics.total_users}
          description={`${analytics.recent_signups} new this week`}
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          title="Active Today"
          value={analytics.active_today}
          description={`${analytics.active_this_week} active this week`}
          icon={<Activity className="h-4 w-4" />}
        />
        <StatCard
          title="Total Prompts"
          value={analytics.total_prompts.toLocaleString()}
          description={`Across ${analytics.total_sessions} sessions`}
          icon={<MessageSquare className="h-4 w-4" />}
        />
        <StatCard
          title="Avg Session Time"
          value={formatDuration(analytics.avg_session_duration)}
          description="Average session duration"
          icon={<Clock className="h-4 w-4" />}
        />
      </div>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Users</CardTitle>
          <CardDescription>
            View detailed analytics for each user
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => handleSort("username")}
                  >
                    Username <SortIcon column="username" />
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => handleSort("email")}
                  >
                    Email <SortIcon column="email" />
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => handleSort("created_at")}
                  >
                    Joined <SortIcon column="created_at" />
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => handleSort("last_login")}
                  >
                    Last Login <SortIcon column="last_login" />
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-muted/50 text-right"
                    onClick={() => handleSort("total_sessions")}
                  >
                    Sessions <SortIcon column="total_sessions" />
                  </TableHead>
                  <TableHead
                    className="cursor-pointer hover:bg-muted/50 text-right"
                    onClick={() => handleSort("total_prompts")}
                  >
                    Prompts <SortIcon column="total_prompts" />
                  </TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedUsers.map((user) => (
                  <TableRow key={user.user_id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        {user.username}
                        {user.is_admin && <Badge variant="outline">Admin</Badge>}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Mail className="h-3 w-3" />
                        {user.email}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-3 w-3 text-muted-foreground" />
                        {formatDate(user.created_at)}
                      </div>
                    </TableCell>
                    <TableCell className="text-sm">
                      {formatDate(user.last_login)}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {user.total_sessions}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {user.total_prompts}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleUserClick(user)}
                      >
                        View Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* User Details Dialog */}
      <Dialog open={!!selectedUser} onOpenChange={() => setSelectedUser(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedUser?.username}
              {selectedUser?.is_admin && <Badge variant="outline">Admin</Badge>}
            </DialogTitle>
            <DialogDescription>{selectedUser?.email}</DialogDescription>
          </DialogHeader>

          {loadingUserDetails ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <>
              {/* User Stats */}
              <div className="grid gap-4 md:grid-cols-4 mb-6">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">{selectedUser?.total_sessions}</div>
                    <p className="text-xs text-muted-foreground mt-1">Total Sessions</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">{selectedUser?.total_prompts}</div>
                    <p className="text-xs text-muted-foreground mt-1">Total Prompts</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">
                      {formatDuration(selectedUser?.avg_session_duration || 0)}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">Avg Session</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">{selectedUser?.total_conversations}</div>
                    <p className="text-xs text-muted-foreground mt-1">Conversations</p>
                  </CardContent>
                </Card>
              </div>

              {/* Tabs for Sessions and Prompts */}
              <Tabs defaultValue="sessions">
                <TabsList className="w-full">
                  <TabsTrigger value="sessions" className="flex-1">
                    Sessions ({userSessions.length})
                  </TabsTrigger>
                  <TabsTrigger value="prompts" className="flex-1">
                    Prompts ({userPrompts.length})
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="sessions" className="mt-4">
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {userSessions.length === 0 ? (
                      <p className="text-center text-muted-foreground py-8">
                        No sessions found
                      </p>
                    ) : (
                      userSessions.map((session) => (
                        <Card key={session.session_id}>
                          <CardContent className="pt-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <div className="flex items-center gap-2 text-sm">
                                  <Clock className="h-4 w-4 text-muted-foreground" />
                                  {formatDateTime(session.started_at)}
                                </div>
                                <div className="text-xs text-muted-foreground mt-1">
                                  Duration: {formatDuration(session.duration_seconds)} •
                                  Prompts: {session.prompt_count}
                                </div>
                              </div>
                              <Badge variant="secondary">
                                {session.ended_at ? "Ended" : "Active"}
                              </Badge>
                            </div>
                          </CardContent>
                        </Card>
                      ))
                    )}
                  </div>
                </TabsContent>

                <TabsContent value="prompts" className="mt-4">
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {userPrompts.length === 0 ? (
                      <p className="text-center text-muted-foreground py-8">
                        No prompts found
                      </p>
                    ) : (
                      userPrompts.map((prompt) => (
                        <Card key={prompt.message_id}>
                          <CardContent className="pt-4">
                            <div className="text-sm mb-2">{prompt.content}</div>
                            <div className="flex items-center justify-between text-xs text-muted-foreground">
                              <span>{formatDateTime(prompt.created_at)}</span>
                              {prompt.conversation_title && (
                                <span className="italic">{prompt.conversation_title}</span>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      ))
                    )}
                  </div>
                </TabsContent>
              </Tabs>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
