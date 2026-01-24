import api from "./api";
import type { Conversation, Message, JudgeResult } from "@/types";

export interface ChatResponse {
  response: string;
  conversation_id: string;
  is_cached: boolean;
  judge_result?: JudgeResult | null;
}

interface ApiMessage {
  message_id?: number;
  role: "user" | "assistant" | "system";
  content: string;
  metadata?: Record<string, unknown>;
}

interface ApiConversation {
  conversation_id: number;
  title?: string | null;
  started_at: string;
  last_activity: string;
  message_count: number;
  messages?: ApiMessage[];
}

// Transform API conversation to our Conversation type
function transformConversation(api: ApiConversation): Conversation {
  return {
    id: String(api.conversation_id),
    title: api.title || `Conversation ${api.conversation_id}`,
    created_at: api.started_at,
    updated_at: api.last_activity,
    message_count: api.message_count,
    messages: api.messages?.map((m, idx) => ({
      id: String(m.message_id || idx),
      role: m.role,
      content: m.content,
      timestamp: new Date().toISOString(),
      is_cached: (m.metadata?.is_cached as boolean) || false,
      judge_result: m.metadata?.judge_result as JudgeResult | null,
    })),
  };
}

export const chatService = {
  async sendMessage(
    message: string,
    conversationId?: string
  ): Promise<ChatResponse> {
    const response = await api.post<{
      response: string;
      conversation_id: number | null;
      is_cached: boolean;
      judge_result?: JudgeResult | null;
    }>("/api/chat/message", {
      message,
      conversation_id: conversationId ? parseInt(conversationId) : undefined,
    });

    return {
      response: response.data.response,
      conversation_id: String(response.data.conversation_id),
      is_cached: response.data.is_cached,
      judge_result: response.data.judge_result,
    };
  },

  async getConversations(): Promise<Conversation[]> {
    const response = await api.get<ApiConversation[]>("/api/chat/conversations");
    return response.data.map(transformConversation);
  },

  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await api.get<ApiConversation>(
      `/api/chat/conversations/${conversationId}`
    );
    return transformConversation(response.data);
  },

  async deleteConversation(conversationId: string): Promise<void> {
    await api.delete(`/api/chat/conversations/${conversationId}`);
  },
};

// Legacy exports for backward compatibility
export const sendMessage = chatService.sendMessage;
export const listConversations = chatService.getConversations;
export const getConversation = chatService.getConversation;
