import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare } from "lucide-react";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { StreamingMessage } from "./StreamingMessage";
import { EmptyState } from "@/components/common/EmptyState";
import { useChat } from "@/hooks/useChat";
import { cn } from "@/lib/utils";

interface ChatContainerProps {
  className?: string;
}

export function ChatContainer({ className }: ChatContainerProps) {
  const {
    messages,
    isLoading,
    isSending,
    isStreaming,
    streamingContent,
    sendMessage,
    cancel,
  } = useChat();

  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, streamingContent]);

  const isEmpty = messages.length === 0 && !isStreaming;

  return (
    <div className={cn("flex h-full flex-col", className)}>
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-3xl px-4 py-6">
          <AnimatePresence mode="wait">
            {isEmpty ? (
              <motion.div
                key="empty"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.2 }}
                className="flex min-h-[60vh] items-center justify-center"
              >
                <EmptyState
                  icon={MessageSquare}
                  title="Start a conversation"
                  description="Ask anything about ServiceNow - configurations, scripting, best practices, or troubleshooting."
                />
              </motion.div>
            ) : (
              <motion.div
                key="messages"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.2 }}
              >
                <MessageList messages={messages} isLoading={isLoading} />

                {/* Streaming message */}
                {isStreaming && (
                  <StreamingMessage content={streamingContent} />
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Scroll anchor */}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="mx-auto max-w-3xl px-4 py-4">
          <ChatInput
            onSubmit={sendMessage}
            onCancel={cancel}
            isLoading={isSending}
            disabled={isLoading}
          />
        </div>
      </div>
    </div>
  );
}
