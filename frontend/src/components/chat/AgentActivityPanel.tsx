import {
  Loader2,
  Check,
  FileText,
  FolderOpen,
  Search,
  ArrowRight,
  Minimize2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { AgentType } from "./MessageBubble";

export interface ActivityStep {
  message: string;
  icon: "search" | "document" | "folder" | "check" | "spinner";
  done: boolean;
  timestamp?: string;
}

interface AgentActivityPanelProps {
  activeAgent: AgentType | "orchestrator";
  activities: ActivityStep[];
  handoff?: { from: AgentType; to: AgentType };
  onMinimize: () => void;
}

const agentInfo: Record<
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

const iconMap = {
  search: Search,
  document: FileText,
  folder: FolderOpen,
  check: Check,
  spinner: Loader2,
};

export function AgentActivityPanel({
  activeAgent,
  activities,
  handoff,
  onMinimize,
}: AgentActivityPanelProps) {
  const agent = agentInfo[activeAgent] ?? agentInfo.consultant;

  return (
    <div className="flex h-full w-80 flex-col border-l border-white/[0.06] bg-card/20 backdrop-blur-2xl shadow-[inset_1px_0_0_0_rgba(255,255,255,0.04)]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.06] px-4 py-3">
        <h3 className="text-sm font-semibold text-foreground">Agent Activity</h3>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-muted-foreground hover:text-foreground"
          onClick={onMinimize}
        >
          <Minimize2 className="h-3.5 w-3.5" />
          <span className="sr-only">Minimize panel</span>
        </Button>
      </div>

      {/* Active agent card */}
      <div className="px-4 py-3">
        <div
          className={cn(
            "flex items-center gap-3 rounded-xl p-3 backdrop-blur-sm border border-white/[0.08] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.06)] animate-pulse-glow",
            agent.bgClass
          )}
        >
          <div
            className={cn(
              "flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold",
              agent.bgClass,
              agent.textClass
            )}
          >
            {agent.letter}
          </div>
          <div>
            <p className={cn("text-sm font-semibold", agent.textClass)}>{agent.label}</p>
            <p className="text-[11px] text-muted-foreground">Active</p>
          </div>
        </div>
      </div>

      {/* Activity feed */}
      <ScrollArea className="flex-1 px-4">
        <div className="flex flex-col gap-2 pb-4">
          {activities.map((step, i) => {
            const Icon = iconMap[step.icon] ?? FileText;
            return (
              <div key={i} className="flex items-start gap-2.5 rounded-lg px-2 py-1.5">
                <div
                  className={cn(
                    "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full",
                    step.done
                      ? "bg-agent-implementation/15 text-agent-implementation"
                      : "bg-primary/10 text-primary"
                  )}
                >
                  {step.done ? (
                    <Check className="h-3 w-3" />
                  ) : step.icon === "spinner" ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Icon className="h-3 w-3" />
                  )}
                </div>
                <div className="flex-1">
                  <span
                    className={cn(
                      "text-xs leading-relaxed",
                      step.done ? "text-muted-foreground" : "text-foreground"
                    )}
                  >
                    {step.message}
                  </span>
                  {step.timestamp && (
                    <p className="text-[10px] text-muted-foreground/60 font-mono">{step.timestamp}</p>
                  )}
                </div>
              </div>
            );
          })}

          {/* Handoff indicator */}
          {handoff && agentInfo[handoff.from] && agentInfo[handoff.to] && (
            <div className="mt-2 flex items-center gap-2 rounded-lg bg-agent-orchestrator/10 backdrop-blur-sm border border-agent-orchestrator/15 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)] p-3">
              <div
                className={cn(
                  "h-6 w-6 rounded-full text-center text-[10px] leading-6 font-bold",
                  agentInfo[handoff.from].bgClass,
                  agentInfo[handoff.from].textClass
                )}
              >
                {agentInfo[handoff.from].letter}
              </div>
              <ArrowRight className="h-4 w-4 text-agent-orchestrator animate-pulse" />
              <div
                className={cn(
                  "h-6 w-6 rounded-full text-center text-[10px] leading-6 font-bold",
                  agentInfo[handoff.to].bgClass,
                  agentInfo[handoff.to].textClass
                )}
              >
                {agentInfo[handoff.to].letter}
              </div>
              <span className="text-[11px] text-agent-orchestrator ml-1">
                Handing off to {agentInfo[handoff.to].label}
              </span>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Tools in use */}
      <div className="border-t border-white/[0.06] px-4 py-3 bg-card/10 backdrop-blur-sm">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
          Tools in use
        </p>
        <div className="flex flex-wrap gap-1.5">
          {["Public Docs", "Internal KB", "Schema Check"].map((tool) => (
            <span
              key={tool}
              className="rounded-md bg-white/[0.04] border border-white/[0.06] backdrop-blur-sm px-2 py-0.5 text-[10px] text-muted-foreground"
            >
              {tool}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
