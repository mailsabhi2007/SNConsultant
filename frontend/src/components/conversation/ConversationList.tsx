import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Loader2 } from "lucide-react";
import { ConversationItem } from "./ConversationItem";
import { EmptyState } from "@/components/common/EmptyState";
import { useConversations } from "@/hooks/useConversations";
import { useChat } from "@/hooks/useChat";

export function ConversationList() {
  const { conversations, isLoading, deleteConversation, isDeleting } =
    useConversations();
  const { activeConversationId, loadConversation } = useChat();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <EmptyState
        icon={MessageSquare}
        title="No conversations"
        description="Start a new chat to begin"
        className="py-8"
      />
    );
  }

  return (
    <div className="space-y-1 px-2 pb-4">
      <AnimatePresence initial={false}>
        {conversations.map((conversation) => (
          <motion.div
            key={conversation.id}
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.15 }}
          >
            <ConversationItem
              conversation={conversation}
              isActive={activeConversationId === conversation.id}
              onSelect={() => loadConversation(conversation.id)}
              onDelete={() => deleteConversation(conversation.id)}
              isDeleting={isDeleting}
            />
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
