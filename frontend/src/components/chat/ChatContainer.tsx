import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare } from "lucide-react";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { StreamingMessage } from "./StreamingMessage";
import { SystemStatusBar } from "./SystemStatusBar";
import { EmptyState } from "@/components/common/EmptyState";
import { useChat } from "@/hooks/useChat";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import { animations } from "@/lib/animations";
import { patterns } from "@/lib/visualEffects";

interface ChatContainerProps {
  className?: string;
}

export function ChatContainer({ className }: ChatContainerProps) {
  const { user } = useAuth();
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

  // Debug logging
  console.log('ChatContainer render - messages:', messages.length, messages);

  // Check if multi-agent is enabled (could be fetched from user settings)
  // For now, we'll assume it's enabled if user exists
  const multiAgentEnabled = !!user;
  // Check if instance is connected (from settings or check last message)
  const instanceConnected = false; // TODO: Check from settings

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, streamingContent]);

  const isEmpty = messages.length === 0 && !isStreaming;
  console.log('isEmpty:', isEmpty, 'messages.length:', messages.length, 'isStreaming:', isStreaming);

  return (
    <div className={cn("flex h-full flex-col relative", className)}>
      {/* Subtle background pattern */}
      <div className={cn("absolute inset-0 opacity-30 dark:opacity-20", patterns.dots)} />

      {/* System Status Bar */}
      <div className="relative z-10">
        <SystemStatusBar
          multiAgentEnabled={multiAgentEnabled}
          instanceConnected={instanceConnected}
        />
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto relative z-10">
        <div className="mx-auto max-w-3xl px-4 py-6">
          {isEmpty ? (
            <div className="flex min-h-[60vh] items-center justify-center">
              <EmptyState
                icon={MessageSquare}
                title="Start a conversation"
                description="Ask anything about ServiceNow - configurations, scripting, best practices, or troubleshooting."
              />
            </div>
          ) : (
            <div>
              <MessageList messages={messages} isLoading={isLoading} />

              {/* Streaming message */}
              {isStreaming && (
                <StreamingMessage content={streamingContent} />
              )}
            </div>
          )}

          {/* Scroll anchor */}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="relative z-10 border-t bg-background/95 backdrop-blur-md supports-[backdrop-filter]:bg-background/60 shadow-[0_-4px_20px_rgba(0,0,0,0.05)] dark:shadow-[0_-4px_20px_rgba(0,0,0,0.3)]">
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
