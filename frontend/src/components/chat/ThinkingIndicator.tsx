import { useEffect, useState } from "react";
import { Loader2, Check, BookOpen, FolderSearch, Wrench } from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import type { AgentType } from "./MessageBubble";

const thinkingMessages: Record<AgentType | "default", string[]> = {
  consultant: [
    "Analyzing your question...",
    "Consulting platform best practices...",
    "Searching documentation...",
    "Reviewing OOB configuration options...",
    "Formulating recommendation...",
  ],
  architect: [
    "Analyzing technical requirements...",
    "Designing solution architecture...",
    "Reviewing code patterns...",
    "Evaluating integration points...",
    "Preparing technical design...",
  ],
  implementation: [
    "Connecting to instance...",
    "Checking live configuration...",
    "Analyzing error logs...",
    "Reviewing recent changes...",
    "Diagnosing issue...",
  ],
  default: [
    "Analyzing your question...",
    "Searching documentation...",
    "Found relevant articles, reviewing...",
    "Checking internal knowledge base...",
    "Formulating response...",
  ],
};

const agentDisplay: Record<
  AgentType | "orchestrator",
  { label: string; bgClass: string; textClass: string; letter: string }
> = {
  consultant: {
    label: "Consultant",
    bgClass: "bg-agent-consultant/15",
    textClass: "text-agent-consultant",
    letter: "C",
  },
  architect: {
    label: "Solution Architect",
    bgClass: "bg-agent-architect/15",
    textClass: "text-agent-architect",
    letter: "S",
  },
  implementation: {
    label: "Implementation",
    bgClass: "bg-agent-implementation/15",
    textClass: "text-agent-implementation",
    letter: "I",
  },
  orchestrator: {
    label: "Orchestrator",
    bgClass: "bg-agent-orchestrator/15",
    textClass: "text-agent-orchestrator",
    letter: "O",
  },
};

interface ToolStatus {
  name: string;
  icon: React.ElementType;
  status: "active" | "done" | "idle";
}

interface ThinkingIndicatorProps {
  agent?: AgentType | "orchestrator";
  activeTools?: string[];
}

export function ThinkingIndicator({ agent = "consultant", activeTools }: ThinkingIndicatorProps) {
  const [messageIndex, setMessageIndex] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  const info = agentDisplay[agent] ?? agentDisplay.consultant;
  const messages = thinkingMessages[agent as AgentType] ?? thinkingMessages.default;

  const tools: ToolStatus[] = [
    {
      name: "Public Docs",
      icon: BookOpen,
      status: activeTools?.includes("Public Docs") ? "active" : "idle",
    },
    {
      name: "Internal KB",
      icon: FolderSearch,
      status: activeTools?.includes("Internal KB") ? "active" : "idle",
    },
    {
      name: "Schema Check",
      icon: Wrench,
      status: activeTools?.includes("Schema Check") ? "active" : "idle",
    },
  ];

  useEffect(() => {
    const msgInterval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % messages.length);
    }, 2500);
    const timeInterval = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);
    return () => {
      clearInterval(msgInterval);
      clearInterval(timeInterval);
    };
  }, [messages.length]);

  return (
    <div className="flex gap-3">
      {/* Agent avatar with spinning ring */}
      <div className={cn("relative flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold", info.bgClass, info.textClass)}>
        {info.letter}
        <div
          className="absolute inset-0 rounded-full border-2 border-transparent animate-spin-slow"
          style={{ borderTopColor: "currentColor" }}
        />
      </div>

      <div className="flex-1 max-w-[85%]">
        <div className="rounded-2xl rounded-tl-sm glass-glow px-4 py-3 animate-pulse-glow animate-border-glow">
          <div className="flex items-center gap-2 mb-2">
            <Badge className={cn("text-[11px] border-0", info.bgClass, info.textClass)}>
              {info.label}
            </Badge>
            <span className="text-[10px] text-muted-foreground">{elapsed}s</span>
          </div>

          {/* Cycling thinking message */}
          <p className="text-sm text-foreground/80 transition-all duration-500">
            {messages[messageIndex]}
          </p>

          {/* Tool chips */}
          <div className="mt-3 flex flex-wrap gap-2">
            {tools.map((tool) => (
              <div
                key={tool.name}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px]",
                  tool.status === "active"
                    ? "bg-primary/10 text-primary"
                    : tool.status === "done"
                      ? "bg-agent-implementation/10 text-agent-implementation"
                      : "bg-muted/60 text-muted-foreground"
                )}
              >
                {tool.status === "active" ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : tool.status === "done" ? (
                  <Check className="h-3 w-3" />
                ) : (
                  <tool.icon className="h-3 w-3" />
                )}
                {tool.name}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
