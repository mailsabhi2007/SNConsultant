import { useState } from "react";
import {
  Copy,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ThumbsUp,
  ThumbsDown,
  ArrowLeft,
  Check,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export type AgentType = "consultant" | "architect" | "implementation";

interface Source {
  name: string;
  type: string;
}

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  agent?: AgentType;
  handoffFrom?: AgentType;
  quality?: number;
  cached?: boolean;
  responseTime?: string;
  sources?: Source[];
  toolsUsed?: string[];
  timestamp?: string;
  creditsUsed?: number;
  onRegenerate?: () => void;
}

const agentConfig: Record<
  AgentType,
  { label: string; bgClass: string; textClass: string; ringClass: string; shadowClass: string }
> = {
  consultant: {
    label: "Consultant",
    bgClass: "bg-agent-consultant/15",
    textClass: "text-agent-consultant",
    ringClass: "ring-agent-consultant/30",
    shadowClass: "shadow-agent-consultant/10",
  },
  architect: {
    label: "Solution Architect",
    bgClass: "bg-agent-architect/15",
    textClass: "text-agent-architect",
    ringClass: "ring-agent-architect/30",
    shadowClass: "shadow-agent-architect/10",
  },
  implementation: {
    label: "Implementation",
    bgClass: "bg-agent-implementation/15",
    textClass: "text-agent-implementation",
    ringClass: "ring-agent-implementation/30",
    shadowClass: "shadow-agent-implementation/10",
  },
};

function renderContent(content: string) {
  return content.split("\n").map((line, i) => {
    if (line.startsWith("### ")) {
      return (
        <h3 key={i} className="mt-3 mb-1 text-sm font-semibold text-foreground">
          {line.replace("### ", "")}
        </h3>
      );
    }
    if (line.startsWith("## ")) {
      return (
        <h2 key={i} className="mt-3 mb-1 text-base font-semibold text-foreground">
          {line.replace("## ", "")}
        </h2>
      );
    }
    if (line.startsWith("- ")) {
      return (
        <div key={i} className="flex gap-2 py-0.5">
          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/60" />
          <span className="text-sm leading-relaxed text-foreground/90">
            {line.replace("- ", "")}
          </span>
        </div>
      );
    }
    if (line.startsWith("```")) return null;
    if (line.trim() === "") return <div key={i} className="h-2" />;
    return (
      <p key={i} className="text-sm leading-relaxed text-foreground/90">
        {line}
      </p>
    );
  });
}

export function MessageBubble({
  role,
  content,
  agent,
  handoffFrom,
  quality,
  cached,
  responseTime,
  sources,
  toolsUsed,
  timestamp,
  creditsUsed,
  onRegenerate,
}: MessageBubbleProps) {
  const [showSources, setShowSources] = useState(false);
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (role === "user") {
    return (
      <div data-testid="message-bubble" className="flex justify-end gap-3">
        <div className="max-w-[70%] rounded-2xl rounded-tr-sm bg-primary/15 backdrop-blur-xl border border-primary/20 px-4 py-3 shadow-[inset_0_1px_0_0_rgba(148,197,233,0.1),0_4px_16px_-4px_rgba(0,0,0,0.3)]">
          <p className="text-sm leading-relaxed text-foreground">{content}</p>
          {timestamp && (
            <p className="mt-1 text-[10px] text-muted-foreground/60 text-right">{timestamp}</p>
          )}
        </div>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/15 backdrop-blur-sm text-primary text-sm font-semibold border border-primary/20 shadow-lg shadow-primary/10">
          U
        </div>
      </div>
    );
  }

  const agentInfo = agent ? agentConfig[agent] : null;

  return (
    <div data-testid="message-bubble" className="flex gap-3 group">
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm ring-2 backdrop-blur-sm shadow-lg",
          agentInfo
            ? `${agentInfo.bgClass} ${agentInfo.textClass} ${agentInfo.ringClass} ${agentInfo.shadowClass}`
            : "bg-primary/15 text-primary ring-primary/30 shadow-primary/10"
        )}
      >
        {agent === "consultant" ? "C" : agent === "architect" ? "S" : agent === "implementation" ? "I" : "A"}
      </div>

      <div className="flex-1 max-w-[85%]">
        <div className="rounded-2xl rounded-tl-sm glass px-4 py-3 transition-all hover:shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08),0_8px_32px_-8px_rgba(0,0,0,0.4)] hover:border-white/[0.12]">
          {/* Agent badge + handoff */}
          <div className="mb-2 flex items-center gap-2">
            {agentInfo && (
              <Badge className={cn("text-[11px] border-0", agentInfo.bgClass, agentInfo.textClass)}>
                {agentInfo.label}
              </Badge>
            )}
            {handoffFrom && agentConfig[handoffFrom] && (
              <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                <ArrowLeft className="h-3 w-3" />
                from {agentConfig[handoffFrom].label}
              </span>
            )}
          </div>

          {/* Content */}
          <div className="prose prose-invert prose-sm max-w-none">
            {renderContent(content)}
          </div>

          {/* Expandable sources */}
          {sources && sources.length > 0 && (
            <div className="mt-3 border-t border-border/30 pt-2">
              <button
                onClick={() => setShowSources(!showSources)}
                className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
              >
                {showSources ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                Research Summary ({sources.length} sources)
              </button>
              {showSources && (
                <div className="mt-2 flex flex-col gap-1.5">
                  {sources.map((source, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                      <span className="h-1 w-1 rounded-full bg-primary/50" />
                      {source.name}
                      <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                        {source.type}
                      </Badge>
                    </div>
                  ))}
                  {toolsUsed && toolsUsed.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {toolsUsed.map((tool) => (
                        <Badge key={tool} variant="secondary" className="text-[10px] px-1.5 py-0">
                          {tool}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Bottom metadata */}
          <div className="mt-3 flex items-center gap-3 border-t border-border/30 pt-2">
            <div className="flex items-center gap-2">
              {quality !== undefined && (
                <Badge
                  className={cn(
                    "text-[10px] border-0",
                    quality >= 80
                      ? "bg-agent-implementation/15 text-agent-implementation"
                      : "bg-agent-orchestrator/15 text-agent-orchestrator"
                  )}
                >
                  {quality >= 80 ? "High Quality" : "Needs Review"} {quality}%
                </Badge>
              )}
              {cached && (
                <Badge variant="secondary" className="text-[10px] border-0">
                  Cached
                </Badge>
              )}
              {creditsUsed !== undefined && (
                <span className="flex items-center gap-0.5 text-[10px] text-muted-foreground/70">
                  <Zap className="h-2.5 w-2.5" />
                  {creditsUsed} {cached ? "(cached)" : "credits"}
                </span>
              )}
            </div>
            <div className="ml-auto flex items-center gap-1">
              {responseTime && (
                <span className="text-[10px] text-muted-foreground mr-2">{responseTime}</span>
              )}
              {timestamp && (
                <span className="text-[10px] text-muted-foreground mr-2">{timestamp}</span>
              )}
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground"
                onClick={handleCopy}
              >
                {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              </Button>
              {onRegenerate && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-foreground"
                  onClick={onRegenerate}
                >
                  <RefreshCw className="h-3 w-3" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="icon"
                className={cn(
                  "h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity",
                  feedback === "up"
                    ? "text-agent-implementation opacity-100"
                    : "text-muted-foreground hover:text-foreground"
                )}
                onClick={() => setFeedback(feedback === "up" ? null : "up")}
              >
                <ThumbsUp className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                className={cn(
                  "h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity",
                  feedback === "down"
                    ? "text-destructive opacity-100"
                    : "text-muted-foreground hover:text-foreground"
                )}
                onClick={() => setFeedback(feedback === "down" ? null : "down")}
              >
                <ThumbsDown className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
