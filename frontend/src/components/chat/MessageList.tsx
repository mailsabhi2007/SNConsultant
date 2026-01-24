import { useRef } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { AnimatePresence } from "framer-motion";
import { Message } from "./Message";
import { Skeleton } from "@/components/ui/skeleton";
import type { Message as MessageType } from "@/types";

interface MessageListProps {
  messages: MessageType[];
  isLoading?: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  // Use virtual scrolling for large message lists
  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 120, // Estimated message height
    overscan: 5,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        {[...Array(3)].map((_, i) => (
          <MessageSkeleton key={i} isAssistant={i % 2 === 1} />
        ))}
      </div>
    );
  }

  // For small message lists, render directly without virtualization
  if (messages.length < 50) {
    return (
      <div className="space-y-6">
        <AnimatePresence initial={false}>
          {messages.map((message, index) => (
            <Message
              key={message.id}
              message={message}
              isLast={index === messages.length - 1}
            />
          ))}
        </AnimatePresence>
      </div>
    );
  }

  // Virtual scrolling for large lists
  return (
    <div ref={parentRef} className="h-full overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: "100%",
          position: "relative",
        }}
      >
        {virtualizer.getVirtualItems().map((virtualRow) => {
          const message = messages[virtualRow.index];
          return (
            <div
              key={virtualRow.key}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <Message
                message={message}
                isLast={virtualRow.index === messages.length - 1}
              />
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MessageSkeleton({ isAssistant }: { isAssistant: boolean }) {
  return (
    <div
      className={`flex gap-3 ${isAssistant ? "justify-start" : "justify-end"}`}
    >
      {isAssistant && <Skeleton className="h-8 w-8 rounded-full" />}
      <div className="space-y-2">
        <Skeleton className="h-4 w-48" />
        <Skeleton className="h-4 w-64" />
        {isAssistant && <Skeleton className="h-4 w-32" />}
      </div>
      {!isAssistant && <Skeleton className="h-8 w-8 rounded-full" />}
    </div>
  );
}
