import { MessageBubble, type AgentType } from "./MessageBubble";
import type { Message as MessageType } from "@/types";

interface MessageProps {
  message: MessageType;
  isLast?: boolean;
}

function mapAgent(currentAgent?: string): AgentType | undefined {
  if (!currentAgent) return undefined;
  if (currentAgent === "solution_architect") return "architect";
  if (currentAgent === "consultant") return "consultant";
  if (currentAgent === "implementation") return "implementation";
  return undefined;
}

export function Message({ message }: MessageProps) {
  if (message.role === "system") return null;

  const agent = mapAgent(message.current_agent);
  const handoffFrom = mapAgent(message.handoff_from);
  const quality = message.judge_result
    ? Math.round((1 - message.judge_result.hallucination_score) * 100)
    : undefined;

  return (
    <MessageBubble
      role={message.role as "user" | "assistant"}
      content={message.content}
      agent={agent}
      handoffFrom={handoffFrom}
      quality={quality}
      cached={message.is_cached}
      timestamp={message.timestamp}
      creditsUsed={message.credits_used}
    />
  );
}
