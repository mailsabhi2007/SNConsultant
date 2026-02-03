import { Badge } from "@/components/ui/badge";
import { Sparkles, Code2, Wrench, GitBranch } from "lucide-react";

interface AgentBadgeProps {
  agent: string;
  size?: "sm" | "md";
}

const AGENT_CONFIG = {
  orchestrator: {
    icon: GitBranch,
    label: "Orchestrator",
    color: "text-purple-600",
    bgColor: "bg-purple-50 border-purple-200",
  },
  consultant: {
    icon: Sparkles,
    label: "Consultant",
    color: "text-blue-600",
    bgColor: "bg-blue-50 border-blue-200",
  },
  solution_architect: {
    icon: Code2,
    label: "Solution Architect",
    color: "text-green-600",
    bgColor: "bg-green-50 border-green-200",
  },
  implementation: {
    icon: Wrench,
    label: "Implementation",
    color: "text-orange-600",
    bgColor: "bg-orange-50 border-orange-200",
  },
};

export function AgentBadge({ agent, size = "sm" }: AgentBadgeProps) {
  const config = AGENT_CONFIG[agent as keyof typeof AGENT_CONFIG];

  if (!config) {
    return null;
  }

  const Icon = config.icon;
  const iconSize = size === "sm" ? "h-3 w-3" : "h-4 w-4";
  const textSize = size === "sm" ? "text-xs" : "text-sm";

  return (
    <Badge variant="outline" className={`${config.bgColor} ${textSize} flex items-center gap-1 font-medium`}>
      <Icon className={`${iconSize} ${config.color}`} />
      <span className={config.color}>{config.label}</span>
    </Badge>
  );
}
