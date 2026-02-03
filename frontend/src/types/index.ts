export interface User {
  id: string;
  email: string;
  is_admin: boolean;
  created_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  is_cached?: boolean;
  judge_result?: JudgeResult | null;
  isStreaming?: boolean;
  current_agent?: string;
  handoff_count?: number;
}

export interface JudgeResult {
  hallucination_score: number;  // 0.0-1.0 (1.0 = high chance of hallucination)
  is_hallucination: boolean;
  reasoning: string;
  flagged_sections?: string[];
  suggested_corrections?: string[];
  judge_model?: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  messages?: Message[];
}

export interface KnowledgeFile {
  id: string;
  filename: string;
  file_size: number;
  chunk_count: number;
  created_at: string;
  user_id: string;
}

export interface Settings {
  servicenow_instance_url?: string;
  servicenow_username?: string;
  servicenow_password?: string;
  theme?: "light" | "dark" | "system";
}

export interface AdminStats {
  total_users: number;
  total_conversations: number;
  total_messages: number;
  total_files: number;
  total_chunks: number;
  cache_stats: {
    hits: number;
    misses: number;
    hit_rate: number;
  };
}

// API response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

// Form types
export interface LoginFormData {
  email: string;
  password: string;
}

export interface RegisterFormData {
  email: string;
  password: string;
  confirmPassword: string;
}
