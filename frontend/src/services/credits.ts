import api from "./api";

export interface CreditBalance {
  balance: number;
  last_transaction_at: string | null;
}

export interface CreditTransaction {
  txn_id: string;
  amount: number;
  type: "grant" | "debit" | "refund";
  description: string | null;
  ref_message_id: string | null;
  tokens_input: number | null;
  tokens_output: number | null;
  model: string | null;
  granted_by: string | null;
  created_at: string;
}

export interface UserCreditBalance {
  user_id: string;
  username: string;
  email: string | null;
  balance: number;
  last_transaction_at: string | null;
  total_debits: number;
}

export interface RateConfig {
  model: string;
  display_name: string;
  credits_per_1k_input_tokens: number;
  credits_per_1k_output_tokens: number;
  api_cost_per_1k_input_usd: number;
  api_cost_per_1k_output_usd: number;
  typical_input_ratio: number;
  is_active: boolean;
  updated_at: string | null;
}

export interface CostEstimate {
  credits: number;
  models: {
    model: string;
    display_name: string;
    estimated_api_cost_usd: number;
    estimated_input_tokens: number;
    estimated_output_tokens: number;
  }[];
  min_cost_usd: number;
  max_cost_usd: number;
  blended_cost_usd: number;
}

export async function getBalance(): Promise<CreditBalance> {
  const res = await api.get<CreditBalance>("/api/credits/balance");
  return res.data;
}

export async function getCreditHistory(limit = 50, offset = 0): Promise<CreditTransaction[]> {
  const res = await api.get<{ transactions: CreditTransaction[] }>("/api/credits/history", {
    params: { limit, offset },
  });
  return res.data.transactions;
}

// Admin endpoints
export async function getAllUserBalances(): Promise<UserCreditBalance[]> {
  const res = await api.get<UserCreditBalance[]>("/api/admin/credits/overview");
  return res.data;
}

export async function assignCredits(user_id: string, amount: number, description?: string) {
  const res = await api.post("/api/admin/credits/assign", { user_id, amount, description });
  return res.data;
}

export async function getUserCreditHistory(user_id: string, limit = 50): Promise<CreditTransaction[]> {
  const res = await api.get<{ transactions: CreditTransaction[] }>(
    `/api/admin/credits/history/${user_id}`,
    { params: { limit } }
  );
  return res.data.transactions;
}

export async function getRateConfig(): Promise<RateConfig[]> {
  const res = await api.get<{ rates: RateConfig[] }>("/api/admin/credits/rates");
  return res.data.rates;
}

export async function updateRateConfig(rates: RateConfig[]) {
  const res = await api.put("/api/admin/credits/rates", { rates });
  return res.data;
}

export async function getCostEstimate(credits: number): Promise<CostEstimate> {
  const res = await api.get<CostEstimate>("/api/admin/credits/cost-estimate", {
    params: { credits },
  });
  return res.data;
}
