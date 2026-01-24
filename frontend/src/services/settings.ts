import api from "./api";
import type { Settings } from "@/types";

interface ApiSettingsResponse {
  configs: Record<string, Record<string, unknown>>;
  user_id?: string;
}

function transformSettings(apiResponse: ApiSettingsResponse): Settings {
  const servicenow = apiResponse.configs?.servicenow || {};
  return {
    servicenow_instance_url: servicenow.instance_url as string | undefined,
    servicenow_username: servicenow.username as string | undefined,
    // Password is stored but we return a placeholder for security
    servicenow_password: servicenow.password ? "••••••••" : undefined,
  };
}

export const settingsService = {
  async getSettings(): Promise<Settings> {
    const response = await api.get<ApiSettingsResponse>("/api/settings/config");
    return transformSettings(response.data);
  },

  async updateSettings(settings: Partial<Settings>): Promise<Settings> {
    // Build bulk update payload
    const servicenowUpdates: Record<string, string> = {};

    if (settings.servicenow_instance_url !== undefined) {
      servicenowUpdates.instance_url = settings.servicenow_instance_url;
    }

    if (settings.servicenow_username !== undefined) {
      servicenowUpdates.username = settings.servicenow_username;
    }

    // Only update password if it's not the placeholder
    if (
      settings.servicenow_password !== undefined &&
      settings.servicenow_password !== "••••••••"
    ) {
      servicenowUpdates.password = settings.servicenow_password;
    }

    // Use bulk update if we have multiple settings
    if (Object.keys(servicenowUpdates).length > 0) {
      await api.put<ApiSettingsResponse>("/api/settings/config/bulk", {
        configs: {
          servicenow: servicenowUpdates,
        },
      });
    }

    // Fetch and return updated settings
    return settingsService.getSettings();
  },
};

// Legacy exports for backward compatibility
export const getSettings = settingsService.getSettings;
export async function updateSetting(
  configType: string,
  configKey: string,
  configValue: unknown
) {
  const response = await api.put<ApiSettingsResponse>("/api/settings/config", {
    config_type: configType,
    config_key: configKey,
    config_value: configValue,
  });
  return response.data;
}
