import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Sparkles,
  Code2,
  Wrench,
  GitBranch,
  Search,
  Database,
  FileText,
  Brain,
  Zap
} from "lucide-react";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";

interface AgentThinkingIndicatorProps {
  agent?: string;
  activity?: string;
}

const AGENT_CONFIG = {
  orchestrator: {
    icon: GitBranch,
    label: "Orchestrator",
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
  },
  consultant: {
    icon: Sparkles,
    label: "Consultant",
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
  },
  solution_architect: {
    icon: Code2,
    label: "Solution Architect",
    color: "text-green-500",
    bgColor: "bg-green-500/10",
  },
  implementation: {
    icon: Wrench,
    label: "Implementation",
    color: "text-orange-500",
    bgColor: "bg-orange-500/10",
  },
};

const THINKING_MESSAGES = {
  orchestrator: [
    "Analyzing your question...",
    "Determining the best specialist...",
    "Routing to the right expert...",
    "Evaluating complexity...",
  ],
  consultant: [
    "Consulting ServiceNow documentation...",
    "Researching best practices...",
    "Checking internal guidelines...",
    "Analyzing your requirements...",
    "Evaluating OOB solutions...",
    "Considering implementation approaches...",
  ],
  solution_architect: [
    "Designing technical solution...",
    "Reviewing code patterns...",
    "Checking schema requirements...",
    "Analyzing integration points...",
    "Evaluating custom approach...",
  ],
  implementation: [
    "Checking instance configuration...",
    "Analyzing error logs...",
    "Reviewing recent changes...",
    "Diagnosing the issue...",
    "Examining system state...",
  ],
};

const TOOL_ACTIVITIES = {
  consult_public_docs: { icon: Search, message: "Searching ServiceNow docs..." },
  consult_user_context: { icon: FileText, message: "Checking your guidelines..." },
  check_live_instance: { icon: Database, message: "Connecting to your instance..." },
  check_table_schema: { icon: Database, message: "Checking table schema..." },
  get_error_logs: { icon: FileText, message: "Analyzing error logs..." },
  request_handoff: { icon: GitBranch, message: "Handing off to specialist..." },
};

export function AgentThinkingIndicator({ agent, activity }: AgentThinkingIndicatorProps) {
  const [currentMessage, setCurrentMessage] = useState("");
  const [messageIndex, setMessageIndex] = useState(0);

  // Get agent configuration
  const currentAgent = agent || "consultant";
  const agentConfig = AGENT_CONFIG[currentAgent as keyof typeof AGENT_CONFIG] || AGENT_CONFIG.consultant;
  const AgentIcon = agentConfig.icon;

  // Cycle through thinking messages
  useEffect(() => {
    if (activity && TOOL_ACTIVITIES[activity as keyof typeof TOOL_ACTIVITIES]) {
      // If we have a specific tool activity, show that
      setCurrentMessage(TOOL_ACTIVITIES[activity as keyof typeof TOOL_ACTIVITIES].message);
      return;
    }

    // Otherwise cycle through agent-specific messages
    const messages = THINKING_MESSAGES[currentAgent as keyof typeof THINKING_MESSAGES] || THINKING_MESSAGES.consultant;

    const interval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length);
    }, 2000);

    return () => clearInterval(interval);
  }, [currentAgent, activity]);

  useEffect(() => {
    if (!activity || !TOOL_ACTIVITIES[activity as keyof typeof TOOL_ACTIVITIES]) {
      const messages = THINKING_MESSAGES[currentAgent as keyof typeof THINKING_MESSAGES] || THINKING_MESSAGES.consultant;
      setCurrentMessage(messages[messageIndex]);
    }
  }, [messageIndex, currentAgent, activity]);

  // Get activity icon if it's a tool
  const ActivityIcon = activity && TOOL_ACTIVITIES[activity as keyof typeof TOOL_ACTIVITIES]
    ? TOOL_ACTIVITIES[activity as keyof typeof TOOL_ACTIVITIES].icon
    : Brain;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex gap-3"
    >
      {/* Agent Avatar */}
      <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${agentConfig.bgColor}`}>
        <AgentIcon className={`h-4 w-4 ${agentConfig.color}`} />
      </div>

      {/* Thinking content */}
      <div className="flex flex-col gap-2">
        {/* Agent badge */}
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs">
            {agentConfig.label}
          </Badge>
        </div>

        {/* Thinking message */}
        <div className="flex items-center gap-3 rounded-2xl rounded-tl-sm bg-muted px-4 py-3">
          <ActivityIcon className="h-4 w-4 text-muted-foreground animate-pulse" />

          <AnimatePresence mode="wait">
            <motion.span
              key={currentMessage}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -5 }}
              transition={{ duration: 0.3 }}
              className="text-sm text-muted-foreground"
            >
              {currentMessage}
            </motion.span>
          </AnimatePresence>

          {/* Animated dots */}
          <div className="flex gap-1">
            <TypingDot delay={0} />
            <TypingDot delay={0.2} />
            <TypingDot delay={0.4} />
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function TypingDot({ delay }: { delay: number }) {
  return (
    <motion.div
      className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40"
      animate={{
        scale: [1, 1.3, 1],
        opacity: [0.4, 1, 0.4],
      }}
      transition={{
        duration: 1,
        repeat: Infinity,
        delay,
      }}
    />
  );
}
