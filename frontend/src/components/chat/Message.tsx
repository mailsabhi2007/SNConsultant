import { useState } from "react";
import { motion } from "framer-motion";
import { Bot, User } from "lucide-react";
import { MessageContent } from "./MessageContent";
import { MessageActions } from "./MessageActions";
import { AgentBadge } from "./AgentBadge";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { animations } from "@/lib/animations";
import { shadows } from "@/lib/visualEffects";
import type { Message as MessageType } from "@/types";

interface MessageProps {
  message: MessageType;
  isLast?: boolean;
}

export function Message({ message, isLast }: MessageProps) {
  const [showActions, setShowActions] = useState(false);
  const isAssistant = message.role === "assistant";
  const isUser = message.role === "user";

  console.log('Message render:', message.role, message.id, message.content.substring(0, 50));

  return (
    <motion.div
      {...animations.fadeInUp}
      className={cn(
        "group relative flex gap-3",
        isUser && "flex-row-reverse"
      )}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      {/* Avatar */}
      <motion.div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-all duration-300",
          isAssistant && "bg-primary/10 text-primary",
          isUser && "bg-muted"
        )}
        whileHover={{ scale: 1.1 }}
      >
        {isAssistant ? (
          <Bot className="h-4 w-4" />
        ) : (
          <User className="h-4 w-4" />
        )}
      </motion.div>

      {/* Message content */}
      <div
        className={cn(
          "flex max-w-[85%] flex-col gap-1",
          isUser && "items-end"
        )}
      >
        {/* Message bubble */}
        <motion.div
          className={cn(
            "rounded-2xl px-4 py-2.5 transition-all duration-300",
            isAssistant && "bg-muted rounded-tl-sm",
            isUser && "bg-primary text-primary-foreground rounded-tr-sm",
            shadows.soft
          )}
          whileHover={{
            y: -2,
            boxShadow: "0 10px 30px rgba(0, 0, 0, 0.1)",
          }}
        >
          <MessageContent
            content={message.content}
            isUser={isUser}
          />
        </motion.div>

        {/* Metadata badges */}
        {isAssistant && (message.current_agent || message.is_cached || message.judge_result) && (
          <div className="flex items-center gap-2 px-1">
            {message.current_agent && (
              <AgentBadge agent={message.current_agent} />
            )}
            {message.is_cached && (
              <Badge variant="secondary" className="text-xs">
                Cached
              </Badge>
            )}
            {message.judge_result && (
              <Badge
                variant={
                  message.judge_result.hallucination_score <= 0.3
                    ? "success"
                    : message.judge_result.hallucination_score <= 0.6
                    ? "warning"
                    : "destructive"
                }
                className="text-xs"
              >
                {message.judge_result.is_hallucination
                  ? "Needs Review"
                  : `Quality: ${Math.round((1 - message.judge_result.hallucination_score) * 100)}%`}
              </Badge>
            )}
          </div>
        )}

        {/* Actions */}
        {isAssistant && (
          <MessageActions
            content={message.content}
            visible={showActions || isLast}
          />
        )}
      </div>
    </motion.div>
  );
}
