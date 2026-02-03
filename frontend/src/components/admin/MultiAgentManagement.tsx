import { useEffect, useState } from "react";
import {
  Users,
  Activity,
  GitBranch,
  Percent,
  RefreshCw,
  CheckCircle,
  XCircle,
  Shield,
  TrendingUp,
  AlertCircle
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import {
  getMultiAgentRollout,
  updateMultiAgentRollout,
  getMultiAgentUsers,
  toggleMultiAgentForUser,
  removeMultiAgentOverride,
  getMultiAgentAnalytics,
  MultiAgentRollout,
  MultiAgentUser,
  MultiAgentAnalytics,
} from "@/services/admin";
import { useToast } from "@/components/ui/use-toast";

export function MultiAgentManagement() {
  const [rollout, setRollout] = useState<MultiAgentRollout | null>(null);
  const [users, setUsers] = useState<MultiAgentUser[]>([]);
  const [analytics, setAnalytics] = useState<MultiAgentAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [rolloutPercentage, setRolloutPercentage] = useState(0);
  const { toast } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [rolloutData, usersData, analyticsData] = await Promise.all([
        getMultiAgentRollout(),
        getMultiAgentUsers(),
        getMultiAgentAnalytics(30),
      ]);

      setRollout(rolloutData);
      setRolloutPercentage(rolloutData.rollout_percentage);
      setUsers(usersData.users);
      setAnalytics(analyticsData);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load multi-agent data",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRolloutUpdate = async () => {
    setIsSaving(true);
    try {
      await updateMultiAgentRollout(rolloutPercentage);
      toast({
        title: "Success",
        description: `Multi-agent rollout updated to ${rolloutPercentage}%`,
      });
      loadData();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to update rollout percentage",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleUserToggle = async (userId: string, currentStatus: boolean) => {
    try {
      await toggleMultiAgentForUser(userId, !currentStatus);
      toast({
        title: "Success",
        description: `Multi-agent ${!currentStatus ? 'enabled' : 'disabled'} for user`,
      });
      loadData();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to toggle multi-agent for user",
        variant: "destructive",
      });
    }
  };

  const handleRemoveOverride = async (userId: string) => {
    try {
      await removeMultiAgentOverride(userId);
      toast({
        title: "Success",
        description: "User override removed, now using system rollout",
      });
      loadData();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to remove override",
        variant: "destructive",
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const usersWithOverride = users.filter(u => u.multi_agent_source === 'override').length;
  const usersEnabled = users.filter(u => u.multi_agent_enabled).length;

  return (
    <div className="space-y-6">
      {/* Alert */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Multi-Agent System Management</AlertTitle>
        <AlertDescription>
          Control the rollout of the multi-agent system to users. Use percentage-based rollout for gradual deployment, or set user-specific overrides for testing.
        </AlertDescription>
      </Alert>

      {/* Analytics Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rollout Status</CardTitle>
            <Percent className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{rollout?.rollout_percentage}%</div>
            <p className="text-xs text-muted-foreground">
              {rollout?.status === 'active' ? 'Active' : 'Disabled'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Users Enabled</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{usersEnabled}</div>
            <p className="text-xs text-muted-foreground">
              {usersWithOverride} with override
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Handoff Rate</CardTitle>
            <GitBranch className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {analytics?.handoff_rate_percentage.toFixed(1)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {analytics?.conversations_with_handoffs} conversations
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Handoffs</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics?.total_handoffs}</div>
            <p className="text-xs text-muted-foreground">
              Last {analytics?.days} days
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Rollout Control */}
      <Card>
        <CardHeader>
          <CardTitle>System Rollout Control</CardTitle>
          <CardDescription>
            Set the percentage of users who will have multi-agent enabled. Uses consistent hashing for stable user assignment.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Rollout Percentage</label>
              <span className="text-2xl font-bold">{rolloutPercentage}%</span>
            </div>
            <Slider
              value={[rolloutPercentage]}
              onValueChange={(value) => setRolloutPercentage(value[0])}
              max={100}
              step={5}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>0% (Disabled)</span>
              <span>50%</span>
              <span>100% (All Users)</span>
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={handleRolloutUpdate}
              disabled={isSaving || rolloutPercentage === rollout?.rollout_percentage}
            >
              {isSaving ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Updating...
                </>
              ) : (
                'Update Rollout'
              )}
            </Button>
            <Button
              variant="outline"
              onClick={() => setRolloutPercentage(0)}
              disabled={isSaving}
            >
              Disable All
            </Button>
            <Button
              variant="outline"
              onClick={() => setRolloutPercentage(100)}
              disabled={isSaving}
            >
              Enable All
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Handoff Analytics */}
      {analytics && analytics.handoff_paths.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Common Handoff Paths</CardTitle>
            <CardDescription>
              Most frequent agent transitions in the last {analytics.days} days
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {analytics.handoff_paths.slice(0, 5).map((path, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{path.from}</Badge>
                    <span className="text-muted-foreground">→</span>
                    <Badge variant="outline">{path.to}</Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{path.count}</span>
                    <span className="text-xs text-muted-foreground">handoffs</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* User Management Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>User Management</CardTitle>
              <CardDescription>
                Control multi-agent access for individual users
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={loadData}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Username</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Multi-Agent</TableHead>
                <TableHead>Source</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.user_id}>
                  <TableCell className="font-medium">{user.username}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {user.is_superadmin && (
                        <Badge variant="default">
                          <Shield className="mr-1 h-3 w-3" />
                          Superadmin
                        </Badge>
                      )}
                      {user.is_admin && !user.is_superadmin && (
                        <Badge variant="secondary">Admin</Badge>
                      )}
                      {!user.is_admin && (
                        <Badge variant="outline">User</Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>
                    {user.is_active ? (
                      <Badge variant="outline" className="bg-green-50">
                        <CheckCircle className="mr-1 h-3 w-3" />
                        Active
                      </Badge>
                    ) : (
                      <Badge variant="outline" className="bg-red-50">
                        <XCircle className="mr-1 h-3 w-3" />
                        Inactive
                      </Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <Switch
                      checked={user.multi_agent_enabled}
                      onCheckedChange={() => handleUserToggle(user.user_id, user.multi_agent_enabled)}
                    />
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={user.multi_agent_source === 'override' ? 'default' : 'secondary'}
                    >
                      {user.multi_agent_source}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    {user.multi_agent_source === 'override' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveOverride(user.user_id)}
                      >
                        Remove Override
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
