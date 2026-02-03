import api from "./api";

export interface AdminStats {
  database: Record<string, unknown>;
  knowledge_base: Record<string, unknown>;
}

export interface SystemAnalytics {
  total_users: number;
  active_today: number;
  active_this_week: number;
  total_sessions: number;
  total_prompts: number;
  avg_session_duration: number;
  total_conversations: number;
  recent_signups: number;
}

export interface UserAnalytics {
  user_id: string;
  username: string;
  email: string;
  is_admin: boolean;
  created_at: string;
  last_login: string | null;
  total_sessions: number;
  total_prompts: number;
  avg_session_duration: number;
  last_activity: string | null;
  total_conversations: number;
}

export interface UserSession {
  session_id: string;
  started_at: string;
  ended_at: string | null;
  last_activity: string;
  prompt_count: number;
  duration_seconds: number;
}

export interface UserPrompt {
  message_id: number;
  conversation_id: number;
  content: string;
  created_at: string;
  conversation_title: string | null;
}

export async function getAdminStats(): Promise<AdminStats> {
  const response = await api.get<AdminStats>("/api/admin/stats");
  return response.data;
}

export async function getSystemAnalytics(): Promise<SystemAnalytics> {
  const response = await api.get<SystemAnalytics>("/api/admin/analytics");
  return response.data;
}

export async function getAllUsersAnalytics(): Promise<UserAnalytics[]> {
  const response = await api.get<UserAnalytics[]>("/api/admin/users");
  return response.data;
}

export async function getUserAnalytics(userId: string): Promise<UserAnalytics> {
  const response = await api.get<UserAnalytics>(`/api/admin/users/${userId}`);
  return response.data;
}

export async function getUserSessions(userId: string, limit: number = 50): Promise<UserSession[]> {
  const response = await api.get<UserSession[]>(`/api/admin/users/${userId}/sessions`, {
    params: { limit },
  });
  return response.data;
}

export async function getUserPrompts(userId: string, limit: number = 100): Promise<UserPrompt[]> {
  const response = await api.get<UserPrompt[]>(`/api/admin/users/${userId}/prompts`, {
    params: { limit },
  });
  return response.data;
}

// Tavily configuration interfaces and functions
export interface TavilyConfig {
  included_domains: string[];
  excluded_domains: string[];
  search_depth: string;
  max_results: number;
  is_user_specific: boolean;
}

export interface TavilyConfigUpdate {
  included_domains?: string[];
  excluded_domains?: string[];
  search_depth?: string;
  max_results?: number;
}

export async function getTavilyConfig(): Promise<TavilyConfig> {
  const response = await api.get<TavilyConfig>("/api/admin/tavily-config");
  return response.data;
}

export async function updateTavilyConfig(config: TavilyConfigUpdate): Promise<{ status: string; config: TavilyConfig }> {
  const response = await api.put<{ status: string; config: TavilyConfig }>("/api/admin/tavily-config", config);
  return response.data;
}

export async function addIncludedDomain(domain: string): Promise<{ status: string; config: TavilyConfig }> {
  const response = await api.post<{ status: string; config: TavilyConfig }>("/api/admin/tavily-config/included-domains", { domain });
  return response.data;
}

export async function removeIncludedDomain(domain: string): Promise<{ status: string; config: TavilyConfig }> {
  const response = await api.delete<{ status: string; config: TavilyConfig }>(`/api/admin/tavily-config/included-domains/${encodeURIComponent(domain)}`);
  return response.data;
}

export async function addExcludedDomain(domain: string): Promise<{ status: string; config: TavilyConfig }> {
  const response = await api.post<{ status: string; config: TavilyConfig }>("/api/admin/tavily-config/excluded-domains", { domain });
  return response.data;
}

export async function removeExcludedDomain(domain: string): Promise<{ status: string; config: TavilyConfig }> {
  const response = await api.delete<{ status: string; config: TavilyConfig }>(`/api/admin/tavily-config/excluded-domains/${encodeURIComponent(domain)}`);
  return response.data;
}

export async function resetTavilyConfig(): Promise<{ status: string; config: TavilyConfig }> {
  const response = await api.post<{ status: string; config: TavilyConfig }>("/api/admin/tavily-config/reset");
  return response.data;
}

// Multi-Agent Management Interfaces and Functions

export interface MultiAgentAnalytics {
  total_handoffs: number;
  handoff_paths: Array<{
    from: string;
    to: string;
    count: number;
  }>;
  conversations_with_handoffs: number;
  total_conversations: number;
  handoff_rate_percentage: number;
  days: number;
}

export interface MultiAgentRollout {
  rollout_percentage: number;
  status: string;
}

export interface MultiAgentUser {
  user_id: string;
  username: string;
  email: string;
  is_admin: boolean;
  is_superadmin: boolean;
  is_active: boolean;
  multi_agent_enabled: boolean;
  multi_agent_source: 'override' | 'rollout';
}

export interface AgentPrompt {
  agent_name: string;
  system_prompt: string | null;
  is_active: boolean;
  updated_at: string | null;
  updated_by: string | null;
}

export interface AgentPromptDetail {
  agent_name: string;
  custom_prompt: string | null;
  is_using_custom: boolean;
  default_prompt: string;
}

export interface MultiAgentConfig {
  config_key: string;
  config_value: string;
  config_type: string;
  description: string | null;
  is_active: boolean;
  updated_at: string | null;
  updated_by: string | null;
}

// Admin endpoints (requires admin role)

export async function getMultiAgentAnalytics(days: number = 30): Promise<MultiAgentAnalytics> {
  const response = await api.get<MultiAgentAnalytics>("/api/admin/multi-agent/analytics", {
    params: { days },
  });
  return response.data;
}

export async function getMultiAgentRollout(): Promise<MultiAgentRollout> {
  const response = await api.get<MultiAgentRollout>("/api/admin/multi-agent/rollout");
  return response.data;
}

export async function updateMultiAgentRollout(percentage: number): Promise<{ status: string; rollout_percentage: number; message: string }> {
  const response = await api.put("/api/admin/multi-agent/rollout", { percentage });
  return response.data;
}

export async function getMultiAgentUsers(): Promise<{ users: MultiAgentUser[]; total_count: number }> {
  const response = await api.get("/api/admin/multi-agent/users");
  return response.data;
}

export async function toggleMultiAgentForUser(userId: string, enabled: boolean): Promise<{ status: string; message: string }> {
  const response = await api.put(`/api/admin/multi-agent/users/${userId}`, { enabled });
  return response.data;
}

export async function removeMultiAgentOverride(userId: string): Promise<{ status: string; message: string }> {
  const response = await api.delete(`/api/admin/multi-agent/users/${userId}/override`);
  return response.data;
}

// Superadmin endpoints (requires superadmin role)

export async function getAllAgentPrompts(): Promise<{ prompts: AgentPrompt[] }> {
  const response = await api.get("/api/admin/multi-agent/prompts");
  return response.data;
}

export async function getAgentPrompt(agentName: string): Promise<AgentPromptDetail> {
  const response = await api.get<AgentPromptDetail>(`/api/admin/multi-agent/prompts/${agentName}`);
  return response.data;
}

export async function updateAgentPrompt(agentName: string, systemPrompt: string): Promise<{ status: string; message: string }> {
  const response = await api.put(`/api/admin/multi-agent/prompts/${agentName}`, {
    system_prompt: systemPrompt,
  });
  return response.data;
}

export async function resetAgentPrompt(agentName: string): Promise<{ status: string; message: string }> {
  const response = await api.post(`/api/admin/multi-agent/prompts/${agentName}/reset`);
  return response.data;
}

export async function getAllMultiAgentConfigs(): Promise<{ configs: MultiAgentConfig[] }> {
  const response = await api.get("/api/admin/multi-agent/config");
  return response.data;
}

export async function updateMultiAgentConfig(
  configKey: string,
  configValue: string,
  configType: string = 'string',
  description?: string
): Promise<{ status: string; message: string }> {
  const response = await api.put(`/api/admin/multi-agent/config/${configKey}`, {
    config_value: configValue,
    config_type: configType,
    description,
  });
  return response.data;
}
