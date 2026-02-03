import { useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useChatStore } from "@/stores/chatStore";
import { chatService } from "@/services/chat";
import type { Message } from "@/types";
import { generateId } from "@/lib/utils";

export function useChat() {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const {
    activeConversationId,
    messages,
    isStreaming,
    streamingContent,
    isSending,
    setActiveConversation,
    setMessages,
    addMessage,
    startStreaming,
    finishStreaming,
    cancelStreaming,
    setLoading,
  } = useChatStore();

  // Main send message function - uses HTTP POST (reliable with cookies)
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isSending) return;

      console.log('=== SEND MESSAGE START ===');
      console.log('activeConversationId:', activeConversationId);
      console.log('content:', content.substring(0, 50));

      setError(null);

      // Add user message immediately
      const userMessage: Message = {
        id: generateId(),
        role: "user",
        content,
        timestamp: new Date().toISOString(),
      };
      console.log('Adding user message to state:', userMessage.id);
      addMessage(userMessage);
      startStreaming();

      try {
        const response = await chatService.sendMessage(
          content,
          activeConversationId || undefined
        );
        console.log('Got response from backend:', response.conversation_id);

        const assistantMessage: Message = {
          id: generateId(),
          role: "assistant",
          content: response.response,
          timestamp: new Date().toISOString(),
          is_cached: response.is_cached,
          judge_result: response.judge_result,
          current_agent: response.current_agent,
          handoff_count: response.handoff_count,
        };

        console.log('Adding assistant message to state:', assistantMessage.id);
        finishStreaming(assistantMessage);

        if (response.conversation_id && !activeConversationId) {
          console.log('Setting new conversation ID:', response.conversation_id);
          // Don't clear messages when setting conversation ID after first message
          setActiveConversation(response.conversation_id, false);
        }

        console.log('Invalidating conversations query');
        queryClient.invalidateQueries({ queryKey: ["conversations"] });
        console.log('=== SEND MESSAGE END ===');
      } catch (err) {
        console.error('Send message error:', err);
        cancelStreaming();
        const errorMessage = err instanceof Error ? err.message : "Failed to send message";
        setError(errorMessage);
      }
    },
    [isSending, addMessage, startStreaming, activeConversationId, finishStreaming, cancelStreaming, setActiveConversation, queryClient]
  );

  // Cancel current request
  const cancel = useCallback(() => {
    cancelStreaming();
  }, [cancelStreaming]);

  // Start new conversation
  const newConversation = useCallback(() => {
    setActiveConversation(null, true);
    setError(null);
  }, [setActiveConversation]);

  // Load conversation
  const loadConversation = useCallback(
    async (conversationId: string) => {
      setLoading(true);
      setError(null);
      try {
        const conversation = await chatService.getConversation(conversationId);
        console.log('Loading conversation', conversationId, 'with messages:', conversation.messages);
        // Don't clear messages with setActiveConversation, we'll set them explicitly
        setActiveConversation(conversationId, false);
        setMessages(conversation.messages || []);
        console.log('Messages set in store');
      } catch (err) {
        console.error('Failed to load conversation:', err);
        setError("Failed to load conversation");
      } finally {
        setLoading(false);
      }
    },
    [setActiveConversation, setLoading, setMessages]
  );

  return {
    messages,
    activeConversationId,
    isLoading: useChatStore.getState().isLoading,
    isSending,
    isStreaming,
    streamingContent,
    error,
    sendMessage,
    cancel,
    newConversation,
    loadConversation,
  };
}
