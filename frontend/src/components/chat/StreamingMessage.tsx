import { motion } from "framer-motion";
import { Bot } from "lucide-react";
import { MessageContent } from "./MessageContent";
import { TypingIndicator } from "./TypingIndicator";

interface StreamingMessageProps {
  content: string;
}

export function StreamingMessage({ content }: StreamingMessageProps) {
  // Show typing indicator if no content yet
  if (!content) {
    return <TypingIndicator />;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-3"
    >
      {/* Avatar */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
        <Bot className="h-4 w-4" />
      </div>

      {/* Message content */}
      <div className="flex max-w-[85%] flex-col gap-1">
        <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-2.5">
          <MessageContent content={content} />

          {/* Blinking cursor */}
          <motion.span
            className="inline-block h-4 w-0.5 bg-primary ml-0.5"
            animate={{ opacity: [1, 0] }}
            transition={{ duration: 0.8, repeat: Infinity }}
          />
        </div>
      </div>
    </motion.div>
  );
}
