import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Save, ExternalLink, Eye, EyeOff, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useSettings } from "@/hooks/useSettings";
import { toast } from "sonner";

const settingsSchema = z.object({
  servicenow_instance_url: z.string().optional(),
  servicenow_username: z.string().optional(),
  servicenow_password: z.string().optional(),
});

type SettingsFormData = z.infer<typeof settingsSchema>;

export function SettingsPage() {
  const { settings, isLoading, updateSettings, isUpdating } = useSettings();
  const [showPassword, setShowPassword] = useState(false);

  const form = useForm<SettingsFormData>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      servicenow_instance_url: "",
      servicenow_username: "",
      servicenow_password: "",
    },
  });

  // Update form when settings are loaded
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
      toast.success("Settings saved successfully");
    } catch (error) {
      toast.error("Failed to save settings");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-2xl px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-muted-foreground">
          Configure your ServiceNow integration settings.
        </p>
      </div>

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* ServiceNow Configuration */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Shield className="h-5 w-5 text-primary" />
              ServiceNow Instance
            </CardTitle>
            <CardDescription>
              Connect your ServiceNow instance to enable direct integrations.
              Credentials are stored securely and used only for API access.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="instance-url" className="text-sm font-medium">
                Instance URL
              </label>
              <Input
                id="instance-url"
                placeholder="your-instance.service-now.com"
                {...form.register("servicenow_instance_url")}
              />
              <p className="text-xs text-muted-foreground">
                Enter your ServiceNow instance URL without the protocol (https://)
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <label htmlFor="sn-username" className="text-sm font-medium">
                  Username
                </label>
                <Input
                  id="sn-username"
                  placeholder="admin"
                  autoComplete="username"
                  {...form.register("servicenow_username")}
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="sn-password" className="text-sm font-medium">
                  Password
                </label>
                <div className="relative">
                  <Input
                    id="sn-password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    autoComplete="current-password"
                    {...form.register("servicenow_password")}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <Eye className="h-4 w-4 text-muted-foreground" />
                    )}
                  </Button>
                </div>
              </div>
            </div>

            <p className="text-xs text-muted-foreground">
              Use a service account with minimal permissions for best security.
              The agent will use these credentials to check logs, schemas, and recent changes.
            </p>

            {form.watch("servicenow_instance_url") && (
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const url = form.getValues("servicenow_instance_url");
                    if (url) {
                      window.open(`https://${url}`, "_blank");
                    }
                  }}
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Open Instance
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Theme Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Appearance</CardTitle>
            <CardDescription>
              Customize the look and feel of the application.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Use the theme toggle in the header to switch between light, dark, and system themes.
            </p>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button type="submit" disabled={isUpdating}>
            {isUpdating ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Save className="mr-2 h-4 w-4" />
            )}
            Save Settings
          </Button>
        </div>
      </form>
    </div>
  );
}
