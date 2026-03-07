import { useEffect, useState, useCallback } from "react";
import {
  Zap,
  Plus,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  Check,
  AlertTriangle,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";
import {
  getAllUserBalances,
  assignCredits,
  getRateConfig,
  updateRateConfig,
  getCostEstimate,
  getUserCreditHistory,
  type UserCreditBalance,
  type RateConfig,
  type CostEstimate,
  type CreditTransaction,
} from "@/services/credits";
import { toast } from "sonner";

// ── Helpers ────────────────────────────────────────────────────────────────────

function formatDate(iso: string | null) {
  if (!iso) return "Never";
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function balanceColor(balance: number) {
  if (balance === 0) return "text-destructive";
  if (balance < 50) return "text-yellow-400";
  return "text-agent-implementation";
}

// ── Assign Credits Modal ───────────────────────────────────────────────────────

interface AssignModalProps {
  open: boolean;
  onClose: () => void;
  preselectedUser: UserCreditBalance | null;
  allUsers: UserCreditBalance[];
  onSuccess: () => void;
}

function AssignModal({ open, onClose, preselectedUser, allUsers, onSuccess }: AssignModalProps) {
  const [selectedUserId, setSelectedUserId] = useState(preselectedUser?.user_id ?? "");
  const [amount, setAmount] = useState(500);
  const [note, setNote] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [estimate, setEstimate] = useState<CostEstimate | null>(null);
  const [loadingEstimate, setLoadingEstimate] = useState(false);
  const [userSearch, setUserSearch] = useState("");

  // Sync preselected user when modal opens
  useEffect(() => {
    if (open) {
      setSelectedUserId(preselectedUser?.user_id ?? "");
      setUserSearch(preselectedUser?.username ?? "");
      setAmount(500);
      setNote("");
    }
  }, [open, preselectedUser]);

  // Fetch cost estimate whenever amount changes
  useEffect(() => {
    if (!open || amount <= 0) return;
    const timer = setTimeout(() => {
      setLoadingEstimate(true);
      getCostEstimate(amount)
        .then(setEstimate)
        .catch(() => {})
        .finally(() => setLoadingEstimate(false));
    }, 400);
    return () => clearTimeout(timer);
  }, [amount, open]);

  const selectedUser = allUsers.find((u) => u.user_id === selectedUserId);

  const filteredUsers = allUsers.filter(
    (u) =>
      u.username.toLowerCase().includes(userSearch.toLowerCase()) ||
      (u.email ?? "").toLowerCase().includes(userSearch.toLowerCase())
  );

  const handleAssign = async () => {
    if (!selectedUserId || amount <= 0) return;
    setIsSaving(true);
    try {
      await assignCredits(selectedUserId, amount, note || undefined);
      toast.success(`${amount.toLocaleString()} credits assigned to ${selectedUser?.username}`);
      onSuccess();
      onClose();
    } catch {
      toast.error("Failed to assign credits");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-primary" />
            Assign Credits
          </DialogTitle>
          <DialogDescription>
            Grant credits to a user. Changes take effect immediately.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4 pt-2">
          {/* User selector */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">User</label>
            <Input
              placeholder="Search by username or email..."
              value={userSearch}
              onChange={(e) => {
                setUserSearch(e.target.value);
                setSelectedUserId("");
              }}
            />
            {userSearch && !selectedUserId && (
              <div className="max-h-40 overflow-y-auto rounded-lg border border-white/[0.08] bg-card/80 backdrop-blur-xl">
                {filteredUsers.length === 0 ? (
                  <p className="px-3 py-2 text-sm text-muted-foreground">No users found</p>
                ) : (
                  filteredUsers.map((u) => (
                    <button
                      key={u.user_id}
                      className="flex w-full items-center justify-between px-3 py-2 text-sm hover:bg-white/[0.04] transition-colors"
                      onClick={() => {
                        setSelectedUserId(u.user_id);
                        setUserSearch(u.username);
                      }}
                    >
                      <span>{u.username}</span>
                      <span className="text-muted-foreground text-xs">{u.email}</span>
                    </button>
                  ))
                )}
              </div>
            )}
            {selectedUser && (
              <div className="flex items-center gap-2 rounded-lg bg-white/[0.04] border border-white/[0.06] px-3 py-2">
                <span className="text-sm font-medium">{selectedUser.username}</span>
                <span className="text-xs text-muted-foreground">{selectedUser.email}</span>
                <span className={cn("ml-auto text-xs font-semibold", balanceColor(selectedUser.balance))}>
                  {selectedUser.balance.toLocaleString()} credits
                </span>
              </div>
            )}
          </div>

          {/* Amount */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">Credits to assign</label>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                min={1}
                value={amount}
                onChange={(e) => setAmount(Math.max(1, parseInt(e.target.value) || 1))}
                className="w-32 tabular-nums"
              />
              <div className="flex gap-1">
                {[100, 500, 1000, 5000].map((q) => (
                  <button
                    key={q}
                    onClick={() => setAmount(q)}
                    className={cn(
                      "rounded-md px-2.5 py-1 text-xs font-medium border transition-colors",
                      amount === q
                        ? "bg-primary/15 text-primary border-primary/30"
                        : "border-white/[0.08] text-muted-foreground hover:text-foreground hover:bg-white/[0.04]"
                    )}
                  >
                    +{q.toLocaleString()}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Cost estimate panel */}
          <div className="rounded-lg border border-white/[0.08] bg-white/[0.02] p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Estimated API Cost at {amount.toLocaleString()} credits
              </span>
              {loadingEstimate && <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />}
            </div>
            {estimate ? (
              <div className="flex flex-col gap-1.5">
                {/* Blended realistic estimate — shown first, most prominent */}
                <div className="flex items-center justify-between rounded-md bg-primary/[0.08] border border-primary/20 px-2.5 py-1.5 mb-0.5">
                  <div>
                    <span className="text-xs font-semibold text-foreground">Realistic cost</span>
                    <span className="text-[10px] text-muted-foreground ml-1.5">85% Sonnet + 15% judge</span>
                  </div>
                  <span className="tabular-nums text-sm font-bold text-primary">
                    ${estimate.blended_cost_usd.toFixed(4)}
                  </span>
                </div>
                {/* Per-model breakdown */}
                {estimate.models.map((m) => (
                  <div key={m.model} className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">{m.display_name}</span>
                    <span className="tabular-nums font-medium">
                      ${m.estimated_api_cost_usd.toFixed(4)}
                    </span>
                  </div>
                ))}
                <div className="mt-1 border-t border-white/[0.06] pt-1.5 flex items-center justify-between text-xs text-muted-foreground">
                  <span>Theoretical range (single model)</span>
                  <span className="tabular-nums">
                    ${estimate.min_cost_usd.toFixed(4)} – ${estimate.max_cost_usd.toFixed(4)}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">Enter an amount to see cost estimate</p>
            )}
          </div>

          {/* Note */}
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium">Note (optional)</label>
            <Input
              placeholder="e.g. Monthly allocation, Trial grant..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-2 pt-1">
            <Button variant="ghost" onClick={onClose} disabled={isSaving}>
              Cancel
            </Button>
            <Button
              onClick={handleAssign}
              disabled={!selectedUserId || amount <= 0 || isSaving}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
            >
              {isSaving ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Assigning...</>
              ) : (
                <><Zap className="mr-2 h-4 w-4" />Assign {amount.toLocaleString()} Credits</>
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ── User History Modal ─────────────────────────────────────────────────────────

interface UserHistoryModalProps {
  open: boolean;
  onClose: () => void;
  user: UserCreditBalance | null;
}

function UserHistoryModal({ open, onClose, user }: UserHistoryModalProps) {
  const [txns, setTxns] = useState<CreditTransaction[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!open || !user) return;
    setLoading(true);
    getUserCreditHistory(user.user_id, 50)
      .then(setTxns)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [open, user]);

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[70vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Credit History — {user?.username}</DialogTitle>
          <DialogDescription>Last 50 transactions</DialogDescription>
        </DialogHeader>
        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : txns.length === 0 ? (
          <p className="text-sm text-muted-foreground py-6 text-center">No transactions yet</p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {txns.map((t) => (
                  <TableRow key={t.txn_id}>
                    <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                      {new Date(t.created_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={cn(
                          "text-[10px] border-0",
                          t.type === "grant"
                            ? "bg-agent-implementation/15 text-agent-implementation"
                            : t.type === "refund"
                            ? "bg-primary/15 text-primary"
                            : "bg-white/[0.06] text-muted-foreground"
                        )}
                      >
                        {t.type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground max-w-[200px] truncate">
                      {t.description ?? "—"}
                    </TableCell>
                    <TableCell className={cn("text-right font-semibold tabular-nums text-sm", t.amount > 0 ? "text-agent-implementation" : "text-muted-foreground")}>
                      {t.amount > 0 ? "+" : ""}{t.amount.toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ── Rate Config Section ────────────────────────────────────────────────────────

interface RateConfigSectionProps {
  isSuperadmin: boolean;
}

function RateConfigSection({ isSuperadmin }: RateConfigSectionProps) {
  const [rates, setRates] = useState<RateConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [edited, setEdited] = useState<Record<string, Partial<RateConfig>>>({});
  const [saving, setSaving] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    getRateConfig()
      .then(setRates)
      .catch(() => toast.error("Failed to load rate config"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const patch = (model: string, field: keyof RateConfig, value: number | boolean) => {
    setEdited((prev) => ({
      ...prev,
      [model]: { ...prev[model], [field]: value },
    }));
  };

  const mergedRates = rates.map((r) => ({ ...r, ...edited[r.model] }));
  const hasChanges = Object.keys(edited).length > 0;

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateRateConfig(mergedRates);
      setEdited({});
      toast.success("Rate config saved");
      load();
    } catch {
      toast.error("Failed to save rate config");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">Model Rate Configuration</CardTitle>
            <CardDescription>
              Credits charged to users and actual API cost (no margin). Prices in USD per 1K tokens.
            </CardDescription>
          </div>
          {isSuperadmin && hasChanges && (
            <Button size="sm" onClick={handleSave} disabled={saving} className="bg-primary text-primary-foreground hover:bg-primary/90">
              {saving ? <Loader2 className="mr-2 h-3 w-3 animate-spin" /> : <Check className="mr-2 h-3 w-3" />}
              Save Changes
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Model</TableHead>
                <TableHead className="text-right">Credits / 1K input</TableHead>
                <TableHead className="text-right">Credits / 1K output</TableHead>
                <TableHead className="text-right">API cost / 1K input ($)</TableHead>
                <TableHead className="text-right">API cost / 1K output ($)</TableHead>
                <TableHead className="text-center">Active</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mergedRates.map((r) => {
                const isEdited = !!edited[r.model];
                return (
                  <TableRow key={r.model} className={isEdited ? "bg-primary/[0.03]" : ""}>
                    <TableCell>
                      <div>
                        <p className="text-sm font-medium">{r.display_name}</p>
                        <p className="text-[10px] text-muted-foreground font-mono">{r.model}</p>
                      </div>
                    </TableCell>
                    {(["credits_per_1k_input_tokens", "credits_per_1k_output_tokens", "api_cost_per_1k_input_usd", "api_cost_per_1k_output_usd"] as const).map((field) => (
                      <TableCell key={field} className="text-right">
                        {isSuperadmin ? (
                          <Input
                            type="number"
                            min={0}
                            step={field.startsWith("api") ? 0.0001 : 0.5}
                            value={r[field] as number}
                            onChange={(e) => patch(r.model, field, parseFloat(e.target.value) || 0)}
                            className="w-24 text-right tabular-nums text-sm ml-auto h-7 px-2"
                          />
                        ) : (
                          <span className="tabular-nums text-sm">{(r[field] as number).toFixed(field.startsWith("api") ? 5 : 1)}</span>
                        )}
                      </TableCell>
                    ))}
                    <TableCell className="text-center">
                      {isSuperadmin ? (
                        <button
                          onClick={() => patch(r.model, "is_active", !r.is_active)}
                          className={cn(
                            "flex h-6 w-10 cursor-pointer items-center rounded-full px-0.5 transition-colors mx-auto",
                            r.is_active ? "bg-primary shadow-lg shadow-primary/20" : "bg-white/[0.08] border border-white/[0.06]"
                          )}
                        >
                          <div className={cn("h-5 w-5 rounded-full bg-foreground transition-transform", r.is_active ? "translate-x-4" : "translate-x-0")} />
                        </button>
                      ) : (
                        <span className={r.is_active ? "text-agent-implementation text-xs" : "text-muted-foreground text-xs"}>
                          {r.is_active ? "Yes" : "No"}
                        </span>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
        {!isSuperadmin && (
          <p className="mt-3 text-xs text-muted-foreground">Rate editing requires superadmin access.</p>
        )}
      </CardContent>
    </Card>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────

export function CreditManagement() {
  const { user } = useAuth();
  const isSuperadmin = !!user?.is_superadmin;

  const [users, setUsers] = useState<UserCreditBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [assignTarget, setAssignTarget] = useState<UserCreditBalance | null>(null);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [historyTarget, setHistoryTarget] = useState<UserCreditBalance | null>(null);
  const [sortField, setSortField] = useState<keyof UserCreditBalance>("balance");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const loadUsers = useCallback(() => {
    setLoading(true);
    getAllUserBalances()
      .then(setUsers)
      .catch(() => toast.error("Failed to load credit balances"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  const handleSort = (field: keyof UserCreditBalance) => {
    if (sortField === field) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortField(field); setSortDir("desc"); }
  };

  const sorted = [...users].sort((a, b) => {
    const av = a[sortField], bv = b[sortField];
    if (av === null || av === undefined) return 1;
    if (bv === null || bv === undefined) return -1;
    const cmp = typeof av === "string" ? av.localeCompare(bv as string) : (av as number) - (bv as number);
    return sortDir === "asc" ? cmp : -cmp;
  });

  const SortIcon = ({ field }: { field: keyof UserCreditBalance }) => {
    if (sortField !== field) return null;
    return sortDir === "asc" ? <ChevronUp className="h-3.5 w-3.5 inline ml-1" /> : <ChevronDown className="h-3.5 w-3.5 inline ml-1" />;
  };

  // Summary stats
  const totalGranted = users.reduce((s, u) => s + Math.max(0, u.balance), 0);
  const zeroBalanceCount = users.filter((u) => u.balance === 0).length;
  const lowBalanceCount = users.filter((u) => u.balance > 0 && u.balance < 50).length;

  return (
    <div className="space-y-6">

      {/* Summary stat cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10">
                <Zap className="h-4 w-4 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">{totalGranted.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">Total credits in circulation</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-yellow-500/10">
                <AlertTriangle className="h-4 w-4 text-yellow-400" />
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">{lowBalanceCount}</p>
                <p className="text-xs text-muted-foreground">Users with low balance (&lt;50)</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-5">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-destructive/10">
                <Zap className="h-4 w-4 text-destructive" />
              </div>
              <div>
                <p className="text-2xl font-bold tabular-nums">{zeroBalanceCount}</p>
                <p className="text-xs text-muted-foreground">Users out of credits</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* User balances table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base">User Credit Balances</CardTitle>
              <CardDescription>Current balance and usage per user</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={loadUsers} disabled={loading} className="border-white/[0.1] bg-white/[0.03]">
                <RefreshCw className={cn("h-3.5 w-3.5 mr-2", loading && "animate-spin")} />
                Refresh
              </Button>
              {isSuperadmin && (
                <Button
                  size="sm"
                  className="bg-primary text-primary-foreground hover:bg-primary/90"
                  onClick={() => { setAssignTarget(null); setShowAssignModal(true); }}
                >
                  <Plus className="h-3.5 w-3.5 mr-2" />
                  Assign Credits
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="cursor-pointer hover:text-foreground" onClick={() => handleSort("username")}>
                      Username <SortIcon field="username" />
                    </TableHead>
                    <TableHead className="cursor-pointer hover:text-foreground" onClick={() => handleSort("email")}>
                      Email <SortIcon field="email" />
                    </TableHead>
                    <TableHead className="cursor-pointer hover:text-foreground text-right" onClick={() => handleSort("balance")}>
                      Balance <SortIcon field="balance" />
                    </TableHead>
                    <TableHead className="cursor-pointer hover:text-foreground text-right" onClick={() => handleSort("total_debits")}>
                      Messages <SortIcon field="total_debits" />
                    </TableHead>
                    <TableHead className="cursor-pointer hover:text-foreground" onClick={() => handleSort("last_transaction_at")}>
                      Last Activity <SortIcon field="last_transaction_at" />
                    </TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sorted.map((u) => (
                    <TableRow key={u.user_id}>
                      <TableCell className="font-medium">{u.username}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{u.email ?? "—"}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Zap className={cn("h-3 w-3", balanceColor(u.balance))} />
                          <span className={cn("font-semibold tabular-nums text-sm", balanceColor(u.balance))}>
                            {u.balance.toLocaleString()}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right tabular-nums text-sm text-muted-foreground">
                        {u.total_debits.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDate(u.last_transaction_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-xs h-7"
                            onClick={() => { setHistoryTarget(u); }}
                          >
                            History
                          </Button>
                          {isSuperadmin && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-xs h-7 text-primary hover:text-primary hover:bg-primary/10"
                              onClick={() => { setAssignTarget(u); setShowAssignModal(true); }}
                            >
                              <Zap className="h-3 w-3 mr-1" />
                              Assign
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Rate config */}
      <RateConfigSection isSuperadmin={isSuperadmin} />

      {/* Modals */}
      <AssignModal
        open={showAssignModal}
        onClose={() => setShowAssignModal(false)}
        preselectedUser={assignTarget}
        allUsers={users}
        onSuccess={loadUsers}
      />
      <UserHistoryModal
        open={!!historyTarget}
        onClose={() => setHistoryTarget(null)}
        user={historyTarget}
      />
    </div>
  );
}
