import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { chatService } from "@/services/chat";
import type { Conversation } from "@/types";

export function useConversations() {
  const queryClient = useQueryClient();

  const {
    data: conversations = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["conversations"],
    queryFn: chatService.getConversations,
    staleTime: 1000 * 60 * 2, // 2 minutes
  });

  const deleteConversationMutation = useMutation({
    mutationFn: chatService.deleteConversation,
    onMutate: async (conversationId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ["conversations"] });

      // Snapshot current value
      const previousConversations = queryClient.getQueryData<Conversation[]>([
        "conversations",
      ]);

      // Optimistically update
      queryClient.setQueryData<Conversation[]>(
        ["conversations"],
        (old) => old?.filter((c) => c.id !== conversationId) || []
      );

      return { previousConversations };
    },
    onError: (err, _, context) => {
      // Rollback on error
      if (context?.previousConversations) {
        queryClient.setQueryData(
          ["conversations"],
          context.previousConversations
        );
      }
    },
    onSettled: () => {
      // Refetch after mutation
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  return {
    conversations,
    isLoading,
    error,
    refetch,
    deleteConversation: deleteConversationMutation.mutate,
    isDeleting: deleteConversationMutation.isPending,
  };
}

export function useConversation(conversationId: string | null) {
  const {
    data: conversation,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["conversation", conversationId],
    queryFn: () =>
      conversationId ? chatService.getConversation(conversationId) : null,
    enabled: !!conversationId,
  });

  return {
    conversation,
    isLoading,
    error,
  };
}
