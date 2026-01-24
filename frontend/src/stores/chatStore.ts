import { create } from "zustand";
import type { Message, Conversation } from "@/types";

interface ChatState {
  // Current conversation
  activeConversationId: string | null;
  messages: Message[];

  // Streaming state
  isStreaming: boolean;
  streamingContent: string;

  // Loading states
  isLoading: boolean;
  isSending: boolean;

  // Actions
  setActiveConversation: (id: string | null, clearMessages?: boolean) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;

  // Streaming actions
  startStreaming: () => void;
  appendStreamContent: (content: string) => void;
  finishStreaming: (message: Message) => void;
  cancelStreaming: () => void;

  // Loading actions
  setLoading: (loading: boolean) => void;
  setSending: (sending: boolean) => void;

  // Reset
  reset: () => void;
}

const initialState = {
  activeConversationId: null,
  messages: [],
  isStreaming: false,
  streamingContent: "",
  isLoading: false,
  isSending: false,
};

export const useChatStore = create<ChatState>((set, get) => ({
  ...initialState,

  setActiveConversation: (id, clearMessages = true) => {
    if (clearMessages) {
      set({ activeConversationId: id, messages: [] });
    } else {
      set({ activeConversationId: id });
    }
  },

  setMessages: (messages) => {
    set({ messages });
  },

  addMessage: (message) => {
    set((state) => ({
      messages: [...state.messages, message],
    }));
  },

  updateMessage: (id, updates) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    }));
  },

  startStreaming: () => {
    set({ isStreaming: true, streamingContent: "", isSending: true });
  },

  appendStreamContent: (content) => {
    set((state) => ({
      streamingContent: state.streamingContent + content,
    }));
  },

  finishStreaming: (message) => {
    set((state) => ({
      isStreaming: false,
      streamingContent: "",
      isSending: false,
      messages: [...state.messages, message],
    }));
  },

  cancelStreaming: () => {
    set({
      isStreaming: false,
      streamingContent: "",
      isSending: false,
    });
  },

  setLoading: (loading) => {
    set({ isLoading: loading });
  },

  setSending: (sending) => {
    set({ isSending: sending });
  },

  reset: () => {
    set(initialState);
  },
}));
