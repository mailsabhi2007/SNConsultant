import { Brain, Lightbulb, Compass, Wrench } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AgentType } from "./MessageBubble";

type AgentOrOrchestrator = AgentType | "orchestrator";

interface AgentNode {
  id: AgentOrOrchestrator;
  label: string;
  icon: React.ElementType;
  bgClass: string;
  textClass: string;
  borderClass: string;
  glowColor: string;
  tags: string[];
}

const agents: AgentNode[] = [
  {
    id: "consultant",
    label: "Consultant",
    icon: Lightbulb,
    bgClass: "bg-agent-consultant/10",
    textClass: "text-agent-consultant",
    borderClass: "border-agent-consultant/30",
    glowColor: "rgba(107, 170, 212, 0.3)",
    tags: ["Best Practices", "OOB Solutions"],
  },
  {
    id: "orchestrator",
    label: "Orchestrator",
    icon: Brain,
    bgClass: "bg-agent-orchestrator/10",
    textClass: "text-agent-orchestrator",
    borderClass: "border-agent-orchestrator/30",
    glowColor: "rgba(212, 202, 90, 0.3)",
    tags: ["Query Routing"],
  },
  {
    id: "architect",
    label: "Solution Architect",
    icon: Compass,
    bgClass: "bg-agent-architect/10",
    textClass: "text-agent-architect",
    borderClass: "border-agent-architect/30",
    glowColor: "rgba(139, 124, 216, 0.3)",
    tags: ["Technical Design", "Code Patterns"],
  },
  {
    id: "implementation",
    label: "Implementation",
    icon: Wrench,
    bgClass: "bg-agent-implementation/10",
    textClass: "text-agent-implementation",
    borderClass: "border-agent-implementation/30",
    glowColor: "rgba(93, 200, 149, 0.3)",
    tags: ["Troubleshooting", "Live Instance"],
  },
];

interface ActivityLogEntry {
  message: string;
  time: string;
}

interface AgentOrchestrationProps {
  activeAgent?: AgentOrOrchestrator;
  activityLog?: ActivityLogEntry[];
}

const defaultActivityLog: ActivityLogEntry[] = [
  { message: "Query received", time: "" },
  { message: "Routing to best specialist...", time: "" },
];

export function AgentOrchestration({
  activeAgent = "orchestrator",
  activityLog = defaultActivityLog,
}: AgentOrchestrationProps) {
  return (
    <div className="px-6 py-4">
      {/* Agent nodes */}
      <div className="flex items-center justify-center gap-4 flex-wrap">
        {agents.map((agent) => {
          const isActive = activeAgent === agent.id;
          const Icon = agent.icon;
          return (
            <div key={agent.id} className="flex flex-col items-center gap-2">
              <div
                className={cn(
                  "relative flex flex-col items-center gap-1.5 rounded-xl border px-4 py-3 transition-all backdrop-blur-xl shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]",
                  agent.borderClass,
                  agent.bgClass,
                  isActive && "scale-105 border-white/[0.15] animate-pulse-glow",
                  !isActive && "hover:bg-white/[0.04] hover:border-white/[0.1]"
                )}
                style={
                  isActive
                    ? { boxShadow: `0 0 20px 4px ${agent.glowColor}` }
                    : undefined
                }
              >
                <div
                  className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-lg",
                    agent.bgClass,
                    agent.textClass
                  )}
                >
                  <Icon className="h-5 w-5" />
                </div>
                <span
                  className={cn(
                    "text-xs font-semibold",
                    isActive ? agent.textClass : "text-muted-foreground"
                  )}
                >
                  {agent.label}
                </span>
                <div className="flex flex-wrap justify-center gap-1">
                  {agent.tags.map((tag) => (
                    <span
                      key={tag}
                      className="rounded bg-muted/60 px-1.5 py-0.5 text-[9px] text-muted-foreground"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
                {isActive && (
                  <span className="text-[9px] text-foreground/60 mt-0.5">Active</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Connecting line */}
      <div className="mt-2 flex items-center justify-center gap-0">
        <div className="h-px w-12 bg-agent-consultant/30" />
        <div className="h-2 w-2 rounded-full bg-agent-consultant/40" />
        <div className="h-px w-20 bg-agent-orchestrator/30" />
        <div className="h-2 w-2 rounded-full bg-agent-orchestrator/40" />
        <div className="h-px w-20 bg-agent-architect/30" />
        <div className="h-2 w-2 rounded-full bg-agent-architect/40" />
        <div className="h-px w-12 bg-agent-implementation/30" />
      </div>

      {/* Activity log */}
      {activityLog.length > 0 && (
        <div className="mt-3 rounded-lg glass-subtle p-3">
          <div className="flex flex-col gap-1">
            {activityLog.map((entry, i) => (
              <div key={i} className="flex items-center gap-2 text-[11px]">
                {entry.time && (
                  <span className="shrink-0 font-mono text-muted-foreground/60">
                    {entry.time}
                  </span>
                )}
                <span className="h-1 w-1 rounded-full bg-primary/40 shrink-0" />
                <span className="text-foreground/70">{entry.message}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
