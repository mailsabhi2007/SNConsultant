import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Plug,
  Eye,
  EyeOff,
  Loader2,
  Check,
  ExternalLink,
  Sun,
  Moon,
  Monitor,
  Settings2,
  Bell,
  Palette,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { useSettings } from "@/hooks/useSettings";
import { toast } from "sonner";

const settingsSchema = z.object({
  servicenow_instance_url: z.string().optional(),
  servicenow_username: z.string().optional(),
  servicenow_password: z.string().optional(),
});

type SettingsFormData = z.infer<typeof settingsSchema>;
type SettingsSection = "general" | "instance" | "appearance" | "notifications";

const sections: { id: SettingsSection; label: string; icon: React.ElementType }[] = [
  { id: "general", label: "General", icon: Settings2 },
  { id: "instance", label: "Platform Connection", icon: Plug },
  { id: "appearance", label: "Appearance", icon: Palette },
  { id: "notifications", label: "Notifications", icon: Bell },
];

export function SettingsPage() {
  const { settings, isLoading, updateSettings, isUpdating } = useSettings();
  const [showPassword, setShowPassword] = useState(false);
  const [activeSection, setActiveSection] = useState<SettingsSection>("instance");
  const [connectionStatus, setConnectionStatus] = useState<"idle" | "testing" | "success" | "error">("idle");
  const [selectedTheme, setSelectedTheme] = useState<"light" | "dark" | "system">("dark");
  const [hasChanges, setHasChanges] = useState(false);

  const form = useForm<SettingsFormData>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      servicenow_instance_url: "",
      servicenow_username: "",
      servicenow_password: "",
    },
  });

  useEffect(() => {
    if (settings) {
      form.reset({
        servicenow_instance_url: settings.servicenow_instance_url || "",
        servicenow_username: settings.servicenow_username || "",
        servicenow_password: settings.servicenow_password || "",
      });
    }
  }, [settings, form]);

  const onSubmit = async (data: SettingsFormData) => {
    try {
      await updateSettings(data);
      setHasChanges(false);
      toast.success("Settings saved successfully");
    } catch {
      toast.error("Failed to save settings");
    }
  };

  const handleTestConnection = () => {
    setConnectionStatus("testing");
    setTimeout(() => {
      setConnectionStatus("success");
      setTimeout(() => setConnectionStatus("idle"), 3000);
    }, 2000);
  };

  const instanceUrl = form.watch("servicenow_instance_url");

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex h-full overflow-hidden">
      {/* Section nav */}
      <nav className="w-56 shrink-0 border-r border-white/[0.06] bg-card/10 backdrop-blur-2xl py-4 px-3 shadow-[inset_-1px_0_0_0_rgba(255,255,255,0.03)]">
        <div className="flex flex-col gap-1">
          {sections.map((sec) => {
            const Icon = sec.icon;
            return (
              <button
                key={sec.id}
                onClick={() => setActiveSection(sec.id)}
                className={cn(
                  "flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors text-left",
                  activeSection === sec.id
                    ? "bg-white/[0.08] text-foreground backdrop-blur-sm shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] border border-white/[0.06]"
                    : "text-muted-foreground hover:bg-white/[0.04] hover:text-foreground border border-transparent"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {sec.label}
              </button>
            );
          })}
        </div>
      </nav>

      {/* Content */}
      <div className="flex-1 overflow-auto relative">
        <div className="max-w-2xl px-8 py-6">

          {/* Instance Section */}
          {activeSection === "instance" && (
            <div>
              <div className="flex items-center gap-3 mb-6">
                <Plug className="h-5 w-5 text-primary" />
                <div>
                  <h2 className="text-lg font-semibold text-foreground">
                    Platform Instance Connection
                  </h2>
                  <p className="text-sm text-muted-foreground">
                    Configure your platform instance credentials
                  </p>
                </div>
              </div>

              {/* Connection status */}
              <div className="mb-6 flex items-center gap-2">
                <span
                  className={cn(
                    "h-2 w-2 rounded-full",
                    instanceUrl ? "bg-agent-implementation" : "bg-destructive"
                  )}
                />
                <span
                  className={cn(
                    "text-xs",
                    instanceUrl ? "text-agent-implementation" : "text-destructive"
                  )}
                >
                  {instanceUrl ? "Connected" : "Not configured"}
                </span>
              </div>

              <div className="flex flex-col gap-5">
                <div className="flex flex-col gap-2">
                  <Label htmlFor="instance-url" className="text-sm text-foreground/80">
                    Instance URL
                  </Label>
                  <Input
                    id="instance-url"
                    placeholder="https://your-instance.service-now.com"
                    className="glass-input focus:border-primary/40"
                    {...form.register("servicenow_instance_url", { onChange: () => setHasChanges(true) })}
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <Label htmlFor="sn-username" className="text-sm text-foreground/80">
                    Username
                  </Label>
                  <Input
                    id="sn-username"
                    placeholder="Service account username"
                    className="glass-input focus:border-primary/40"
                    {...form.register("servicenow_username", { onChange: () => setHasChanges(true) })}
                  />
                  <p className="text-[11px] text-muted-foreground">
                    Use a service account with appropriate permissions
                  </p>
                </div>

                <div className="flex flex-col gap-2">
                  <Label htmlFor="sn-password" className="text-sm text-foreground/80">
                    Password
                  </Label>
                  <div className="relative">
                    <Input
                      id="sn-password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Instance password"
                      className="pr-10 glass-input focus:border-primary/40"
                      {...form.register("servicenow_password", { onChange: () => setHasChanges(true) })}
                    />
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <Button
                    variant="outline"
                    onClick={handleTestConnection}
                    disabled={connectionStatus === "testing"}
                    className="border-white/[0.1] bg-white/[0.03] backdrop-blur-sm hover:bg-white/[0.06]"
                  >
                    {connectionStatus === "testing" ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Testing...</>
                    ) : connectionStatus === "success" ? (
                      <><Check className="mr-2 h-4 w-4 text-agent-implementation" />Connection Successful</>
                    ) : connectionStatus === "error" ? (
                      <><X className="mr-2 h-4 w-4 text-destructive" />Connection Failed</>
                    ) : (
                      "Test Connection"
                    )}
                  </Button>
                  {instanceUrl && (
                    <Button
                      variant="secondary"
                      onClick={() => window.open(`https://${instanceUrl}`, "_blank")}
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      Open Instance
                    </Button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* General Section */}
          {activeSection === "general" && (
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-2">General Settings</h2>
              <p className="text-sm text-muted-foreground mb-6">
                Configure general application preferences
              </p>
              <div className="flex flex-col gap-5">
                <div className="flex flex-col gap-2">
                  <Label className="text-sm text-foreground/80">Default Agent</Label>
                  <div className="flex flex-wrap gap-2">
                    {["Auto (Orchestrator)", "Consultant", "Solution Architect", "Implementation"].map((a) => (
                      <Button
                        key={a}
                        variant={a === "Auto (Orchestrator)" ? "default" : "secondary"}
                        size="sm"
                        className={cn(
                          "text-xs",
                          a === "Auto (Orchestrator)" && "bg-primary/15 text-primary hover:bg-primary/25 border border-primary/20"
                        )}
                      >
                        {a}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Appearance Section */}
          {activeSection === "appearance" && (
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-2">Appearance</h2>
              <p className="text-sm text-muted-foreground mb-6">
                Customize the look and feel of the application
              </p>
              <div className="grid grid-cols-3 gap-4">
                {(
                  [
                    { id: "light" as const, label: "Light", icon: Sun },
                    { id: "dark" as const, label: "Dark", icon: Moon },
                    { id: "system" as const, label: "System", icon: Monitor },
                  ]
                ).map((theme) => {
                  const Icon = theme.icon;
                  const isActive = selectedTheme === theme.id;
                  return (
                    <button
                      key={theme.id}
                      onClick={() => { setSelectedTheme(theme.id); setHasChanges(true); }}
                      className={cn(
                        "relative flex flex-col items-center gap-3 rounded-xl border p-6 transition-all backdrop-blur-xl",
                        isActive
                          ? "border-primary/40 bg-primary/[0.08] shadow-[inset_0_1px_0_0_rgba(148,197,233,0.1),0_8px_32px_-8px_rgba(0,0,0,0.3)]"
                          : "border-white/[0.08] bg-card/15 hover:border-white/[0.15] hover:bg-card/25"
                      )}
                    >
                      {isActive && (
                        <div className="absolute top-2 right-2 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground">
                          <Check className="h-3 w-3" />
                        </div>
                      )}
                      <div
                        className={cn(
                          "flex h-12 w-12 items-center justify-center rounded-lg",
                          isActive ? "bg-primary/15 text-primary" : "bg-muted text-muted-foreground"
                        )}
                      >
                        <Icon className="h-6 w-6" />
                      </div>
                      <span
                        className={cn(
                          "text-sm font-medium",
                          isActive ? "text-foreground" : "text-muted-foreground"
                        )}
                      >
                        {theme.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Notifications Section */}
          {activeSection === "notifications" && (
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-2">Notifications</h2>
              <p className="text-sm text-muted-foreground mb-6">
                Manage your notification preferences
              </p>
              <div className="flex flex-col gap-4">
                {[
                  { label: "Agent handoff alerts", desc: "Get notified when an agent hands off to another", enabled: true },
                  { label: "Response quality warnings", desc: "Alert when a response is flagged for review", enabled: true },
                  { label: "Knowledge base updates", desc: "Notify when new documents are indexed", enabled: false },
                  { label: "System status changes", desc: "Alert on API health or connection changes", enabled: true },
                ].map((notif) => (
                  <div
                    key={notif.label}
                    className="flex items-center justify-between rounded-lg glass-subtle px-4 py-3"
                  >
                    <div>
                      <p className="text-sm font-medium text-foreground">{notif.label}</p>
                      <p className="text-[11px] text-muted-foreground">{notif.desc}</p>
                    </div>
                    <div
                      className={cn(
                        "flex h-6 w-10 cursor-pointer items-center rounded-full px-0.5 transition-colors",
                        notif.enabled
                          ? "bg-primary shadow-lg shadow-primary/20"
                          : "bg-white/[0.08] border border-white/[0.06]"
                      )}
                    >
                      <div
                        className={cn(
                          "h-5 w-5 rounded-full bg-foreground transition-transform",
                          notif.enabled ? "translate-x-4" : "translate-x-0"
                        )}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Sticky save bar */}
        {hasChanges && (
          <div className="sticky bottom-0 border-t border-white/[0.08] bg-card/30 backdrop-blur-2xl px-8 py-3 shadow-[0_-8px_32px_-8px_rgba(0,0,0,0.3),inset_0_1px_0_0_rgba(255,255,255,0.06)]">
            <div className="max-w-2xl flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-agent-orchestrator animate-pulse" />
                <span className="text-xs text-agent-orchestrator">Unsaved changes</span>
              </div>
              <div className="flex items-center gap-3">
                <button
                  className="text-xs text-muted-foreground hover:text-foreground transition-colors"
                  onClick={() => { form.reset(); setHasChanges(false); }}
                >
                  Discard Changes
                </button>
                <Button
                  size="sm"
                  className="bg-primary text-primary-foreground hover:bg-primary/90"
                  onClick={form.handleSubmit(onSubmit)}
                  disabled={isUpdating}
                >
                  {isUpdating ? <Loader2 className="mr-2 h-3 w-3 animate-spin" /> : null}
                  Save Settings
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
