import api from "./api";

export interface AdminStats {
  database: Record<string, unknown>;
  knowledge_base: Record<string, unknown>;
}

export async function getAdminStats(): Promise<AdminStats> {
  const response = await api.get<AdminStats>("/api/admin/stats");
  return response.data;
}
