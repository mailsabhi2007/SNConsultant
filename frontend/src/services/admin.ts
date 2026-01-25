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
