import { motion } from "framer-motion";
import { Bot, Sparkles, Code2, Wrench } from "lucide-react";
import { MessageContent } from "./MessageContent";
import { AgentThinkingIndicator } from "./AgentThinkingIndicator";
import { AgentBadge } from "./AgentBadge";

interface StreamingMessageProps {
  content: string;
  agent?: string;
  activity?: string;
}

const AGENT_ICONS = {
  consultant: Sparkles,
  solution_architect: Code2,
  implementation: Wrench,
  orchestrator: Bot,
};

const AGENT_COLORS = {
  consultant: "bg-blue-500/10 text-blue-500",
  solution_architect: "bg-green-500/10 text-green-500",
  implementation: "bg-orange-500/10 text-orange-500",
  orchestrator: "bg-purple-500/10 text-purple-500",
};

export function StreamingMessage({ content, agent, activity }: StreamingMessageProps) {
  // Show agent thinking indicator if no content yet
  if (!content) {
    return <AgentThinkingIndicator agent={agent} activity={activity} />;
  }

  // Get agent-specific icon and colors
  const currentAgent = agent || "consultant";
  const AgentIcon = AGENT_ICONS[currentAgent as keyof typeof AGENT_ICONS] || Bot;
  const agentColor = AGENT_COLORS[currentAgent as keyof typeof AGENT_COLORS] || "bg-primary/10 text-primary";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex gap-3"
    >
      {/* Agent Avatar */}
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${agentColor}`}>
        <AgentIcon className="h-4 w-4" />
      </div>

      {/* Message content */}
      <div className="flex max-w-[85%] flex-col gap-1">
        {/* Agent badge */}
        {agent && (
          <div className="px-1">
            <AgentBadge agent={agent} />
          </div>
        )}

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
