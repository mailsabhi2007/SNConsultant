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
  Search,
  Plus,
  X,
  RefreshCw,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
  getTavilyConfig,
  updateTavilyConfig,
  addIncludedDomain,
  removeIncludedDomain,
  addExcludedDomain,
  removeExcludedDomain,
  resetTavilyConfig,
  SystemAnalytics,
  UserAnalytics,
  UserSession,
  UserPrompt,
  TavilyConfig,
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

  // Tavily config state
  const [tavilyConfig, setTavilyConfig] = useState<TavilyConfig | null>(null);
  const [loadingTavily, setLoadingTavily] = useState(false);
  const [newIncludedDomain, setNewIncludedDomain] = useState("");
  const [newExcludedDomain, setNewExcludedDomain] = useState("");
  const [tavilyError, setTavilyError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getSystemAnalytics(), getAllUsersAnalytics(), getTavilyConfig()])
      .then(([analyticsData, usersData, tavilyData]) => {
        setAnalytics(analyticsData);
        setUsers(usersData);
        setTavilyConfig(tavilyData);
      })
      .catch(() => {
        setError("Failed to load admin analytics");
      })
      .finally(() => setIsLoading(false));
  }, []);

  const handleAddIncludedDomain = async () => {
    if (!newIncludedDomain.trim()) return;

    setLoadingTavily(true);
    setTavilyError(null);
    try {
      const result = await addIncludedDomain(newIncludedDomain.trim());
      setTavilyConfig(result.config);
      setNewIncludedDomain("");
    } catch (err) {
      setTavilyError("Failed to add domain");
    } finally {
      setLoadingTavily(false);
    }
  };

  const handleRemoveIncludedDomain = async (domain: string) => {
    setLoadingTavily(true);
    setTavilyError(null);
    try {
      const result = await removeIncludedDomain(domain);
      setTavilyConfig(result.config);
    } catch (err) {
      setTavilyError("Failed to remove domain");
    } finally {
      setLoadingTavily(false);
    }
  };

  const handleAddExcludedDomain = async () => {
    if (!newExcludedDomain.trim()) return;

    setLoadingTavily(true);
    setTavilyError(null);
    try {
      const result = await addExcludedDomain(newExcludedDomain.trim());
      setTavilyConfig(result.config);
      setNewExcludedDomain("");
    } catch (err) {
      setTavilyError("Failed to add domain");
    } finally {
      setLoadingTavily(false);
    }
  };

  const handleRemoveExcludedDomain = async (domain: string) => {
    setLoadingTavily(true);
    setTavilyError(null);
    try {
      const result = await removeExcludedDomain(domain);
      setTavilyConfig(result.config);
    } catch (err) {
      setTavilyError("Failed to remove domain");
    } finally {
      setLoadingTavily(false);
    }
  };

  const handleResetTavilyConfig = async () => {
    if (!confirm("Are you sure you want to reset Tavily configuration to defaults?")) return;

    setLoadingTavily(true);
    setTavilyError(null);
    try {
      const result = await resetTavilyConfig();
      setTavilyConfig(result.config);
    } catch (err) {
      setTavilyError("Failed to reset configuration");
    } finally {
      setLoadingTavily(false);
    }
  };

  const handleUpdateSearchDepth = async (depth: string) => {
    setLoadingTavily(true);
    setTavilyError(null);
    try {
      const result = await updateTavilyConfig({ search_depth: depth });
      setTavilyConfig(result.config);
    } catch (err) {
      setTavilyError("Failed to update search depth");
    } finally {
      setLoadingTavily(false);
    }
  };

  const handleUpdateMaxResults = async (maxResults: number) => {
    setLoadingTavily(true);
    setTavilyError(null);
    try {
      const result = await updateTavilyConfig({ max_results: maxResults });
      setTavilyConfig(result.config);
    } catch (err) {
      setTavilyError("Failed to update max results");
    } finally {
      setLoadingTavily(false);
    }
  };

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

      {/* Tavily Configuration */}
      <Card className="mt-8">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Tavily AI Search Configuration
              </CardTitle>
              <CardDescription>
                Configure search sources and domains for Tavily AI web search
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleResetTavilyConfig}
              disabled={loadingTavily}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Reset to Defaults
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {tavilyError && (
            <div className="mb-4 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              {tavilyError}
            </div>
          )}

          {tavilyConfig && (
            <div className="space-y-6">
              {/* Search Settings */}
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="text-sm font-medium mb-2 block">Search Depth</label>
                  <div className="flex gap-2">
                    <Button
                      variant={tavilyConfig.search_depth === "basic" ? "default" : "outline"}
                      size="sm"
                      onClick={() => handleUpdateSearchDepth("basic")}
                      disabled={loadingTavily}
                    >
                      Basic
                    </Button>
                    <Button
                      variant={tavilyConfig.search_depth === "advanced" ? "default" : "outline"}
                      size="sm"
                      onClick={() => handleUpdateSearchDepth("advanced")}
                      disabled={loadingTavily}
                    >
                      Advanced
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    Basic: Faster, less comprehensive. Advanced: Slower, more thorough.
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Max Results</label>
                  <Input
                    type="number"
                    min={1}
                    max={20}
                    value={tavilyConfig.max_results}
                    onChange={(e) => {
                      const val = parseInt(e.target.value);
                      if (val >= 1 && val <= 20) {
                        handleUpdateMaxResults(val);
                      }
                    }}
                    disabled={loadingTavily}
                  />
                  <p className="text-xs text-muted-foreground mt-1">
                    Maximum number of search results (1-20)
                  </p>
                </div>
              </div>

              {/* Included Domains */}
              <div>
                <label className="text-sm font-medium mb-2 block">Included Domains</label>
                <p className="text-xs text-muted-foreground mb-3">
                  Restrict search results to only these domains. Leave empty to search all sources.
                </p>
                <div className="flex gap-2 mb-3">
                  <Input
                    placeholder="e.g., servicenow.com"
                    value={newIncludedDomain}
                    onChange={(e) => setNewIncludedDomain(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        handleAddIncludedDomain();
                      }
                    }}
                    disabled={loadingTavily}
                  />
                  <Button
                    onClick={handleAddIncludedDomain}
                    disabled={loadingTavily || !newIncludedDomain.trim()}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {tavilyConfig.included_domains.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No included domains configured</p>
                  ) : (
                    tavilyConfig.included_domains.map((domain) => (
                      <Badge key={domain} variant="secondary" className="flex items-center gap-1">
                        {domain}
                        <button
                          onClick={() => handleRemoveIncludedDomain(domain)}
                          disabled={loadingTavily}
                          className="ml-1 hover:text-destructive"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))
                  )}
                </div>
              </div>

              {/* Excluded Domains */}
              <div>
                <label className="text-sm font-medium mb-2 block">Excluded Domains</label>
                <p className="text-xs text-muted-foreground mb-3">
                  Block search results from these domains.
                </p>
                <div className="flex gap-2 mb-3">
                  <Input
                    placeholder="e.g., wikipedia.org"
                    value={newExcludedDomain}
                    onChange={(e) => setNewExcludedDomain(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        handleAddExcludedDomain();
                      }
                    }}
                    disabled={loadingTavily}
                  />
                  <Button
                    onClick={handleAddExcludedDomain}
                    disabled={loadingTavily || !newExcludedDomain.trim()}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {tavilyConfig.excluded_domains.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No excluded domains configured</p>
                  ) : (
                    tavilyConfig.excluded_domains.map((domain) => (
                      <Badge key={domain} variant="destructive" className="flex items-center gap-1">
                        {domain}
                        <button
                          onClick={() => handleRemoveExcludedDomain(domain)}
                          disabled={loadingTavily}
                          className="ml-1 hover:text-destructive-foreground/70"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
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
