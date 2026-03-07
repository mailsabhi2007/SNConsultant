import { useEffect, useRef, useState } from "react";
import { MessageSquare, PanelRightClose, PanelRightOpen } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { AgentActivityPanel, type ActivityStep } from "./AgentActivityPanel";
import { AgentOrchestration } from "./AgentOrchestration";
import { EmptyState } from "@/components/common/EmptyState";
import { useChat } from "@/hooks/useChat";
import { useAuth } from "@/hooks/useAuth";
import { useSettings } from "@/hooks/useSettings";
import { cn } from "@/lib/utils";
import type { AgentType } from "./MessageBubble";

interface ChatContainerProps {
  className?: string;
}

function mapAgent(currentAgent?: string): AgentType | "orchestrator" {
  if (!currentAgent) return "orchestrator";
  if (currentAgent === "solution_architect") return "architect";
  if (currentAgent === "consultant") return "consultant";
  if (currentAgent === "implementation") return "implementation";
  return "orchestrator";
}

function mapAgentType(agent?: string): AgentType | undefined {
  if (agent === "solution_architect") return "architect";
  if (agent === "consultant") return "consultant";
  if (agent === "implementation") return "implementation";
  return undefined;
}

const AGENT_LABELS: Record<string, string> = {
  consultant: "Consultant",
  solution_architect: "Solution Architect",
  architect: "Solution Architect",
  implementation: "Implementation",
  orchestrator: "Orchestrator",
};

export function ChatContainer({ className }: ChatContainerProps) {
  const { user } = useAuth();
  const { settings } = useSettings();
  const {
    messages,
    isLoading,
    isSending,
    isStreaming,
    streamingContent,
    sendMessage,
    cancel,
    error,
  } = useChat();

  const [showPanel, setShowPanel] = useState(true);
  const [showOrchestration, setShowOrchestration] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const multiAgentEnabled = !!user;
  const instanceConnected = !!settings?.servicenow_instance_url;

  // Derive active agent from last assistant message
  const lastAssistantMsg = [...messages].reverse().find((m) => m.role === "assistant");
  const activeAgent = mapAgent(lastAssistantMsg?.current_agent);

  // Build activity log from messages
  const activityLog = messages
    .filter((m) => m.role === "assistant" && m.current_agent)
    .slice(-5)
    .map((m) => ({
      message: `${AGENT_LABELS[m.current_agent!] ?? m.current_agent} responded`,
      time: m.timestamp || "",
    }));

  // Build activity steps based on current state
  const activities: ActivityStep[] = isSending
    ? [
        { message: "Analyzing query context...", icon: "check" as const, done: true },
        { message: "Routing to specialist...", icon: "check" as const, done: true },
        { message: "Searching documentation...", icon: "spinner" as const, done: false },
      ]
    : lastAssistantMsg
    ? [
        { message: "Query analyzed", icon: "check" as const, done: true },
        { message: "Documentation searched", icon: "check" as const, done: true },
        { message: "Response generated", icon: "check" as const, done: true },
      ]
    : [];

  // Derive handoff from the most recent assistant message that has handoff_from set
  const lastHandoffMsg = [...messages]
    .reverse()
    .find((m) => m.role === "assistant" && m.handoff_from);
  const handoffInfo =
    lastHandoffMsg?.handoff_from
      ? {
          from: mapAgentType(lastHandoffMsg.handoff_from) ?? ("consultant" as AgentType),
          to: mapAgentType(lastHandoffMsg.current_agent) ?? ("architect" as AgentType),
        }
      : undefined;

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamingContent, isSending]);

  const isEmpty = messages.length === 0 && !isStreaming && !isSending;

  return (
    <div className={cn("flex h-full", className)}>
      {/* Main chat area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex items-center justify-between border-b border-white/[0.06] bg-card/20 backdrop-blur-xl px-6 py-3 shrink-0">
          <div className="flex items-center gap-3">
            {multiAgentEnabled && (
              <Badge className="bg-agent-implementation/10 text-agent-implementation border border-agent-implementation/20 text-xs backdrop-blur-sm">
                <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-agent-implementation animate-pulse" />
                Multi-Agent System Active
              </Badge>
            )}
            <Badge
              variant="secondary"
              className="text-xs border-white/[0.08] bg-white/[0.04] backdrop-blur-sm"
            >
              {instanceConnected ? "Instance: Connected" : "Instance: Not configured"}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-muted-foreground hover:text-foreground"
              onClick={() => setShowOrchestration(!showOrchestration)}
            >
              {showOrchestration ? "Hide" : "Show"} Agent Flow
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
              onClick={() => setShowPanel(!showPanel)}
            >
              {showPanel ? (
                <PanelRightClose className="h-4 w-4" />
              ) : (
                <PanelRightOpen className="h-4 w-4" />
              )}
              <span className="sr-only">Toggle activity panel</span>
            </Button>
          </div>
        </header>

        {/* Agent orchestration panel */}
        {showOrchestration && (
          <div className="border-b border-white/[0.06] bg-card/10 backdrop-blur-xl shrink-0">
            <AgentOrchestration
              activeAgent={isSending ? "orchestrator" : activeAgent}
              activityLog={activityLog}
            />
          </div>
        )}

        {/* Messages */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto"
        >
          <div className="mx-auto max-w-3xl px-6 py-6">
            {isEmpty ? (
              <div className="relative flex min-h-[60vh] items-center justify-center">
                <EmptyState
                  icon={MessageSquare}
                  title="Start a conversation"
                  description="Ask anything — configurations, integrations, best practices, or troubleshooting."
                />
                <span className="absolute bottom-4 right-0 text-[10px] text-muted-foreground/40 select-none">
                  Optimized for ServiceNow
                </span>
              </div>
            ) : (
              <div className="flex flex-col gap-6">
                <MessageList messages={messages} isLoading={isLoading} />

                {/* Streaming content shown inline */}
                {isStreaming && streamingContent && (
                  <div className="flex gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary text-sm ring-2 ring-primary/30">
                      A
                    </div>
                    <div className="flex-1 max-w-[85%]">
                      <div className="rounded-2xl rounded-tl-sm glass px-4 py-3">
                        <p className="text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap">
                          {streamingContent}
                        </p>
                        <span className="inline-block w-1.5 h-4 bg-primary/60 animate-pulse ml-0.5" />
                      </div>
                    </div>
                  </div>
                )}

                {/* Thinking indicator when sending but not yet streaming */}
                {isSending && !isStreaming && (
                  <ThinkingIndicator agent={activeAgent} />
                )}
              </div>
            )}
          </div>
        </div>

        {/* Input area */}
        <div className="border-t border-white/[0.06] bg-card/10 backdrop-blur-xl px-6 py-4 shrink-0">
          <div className="mx-auto max-w-3xl">
            {error && (
              <p className="mb-2 rounded-lg border border-destructive/40 bg-destructive/10 px-4 py-2 text-sm text-destructive">
                {error}
              </p>
            )}
            <div className="relative rounded-xl glass-glow focus-within:border-primary/30 focus-within:shadow-[inset_0_1px_0_0_rgba(255,255,255,0.08),0_0_0_1px_rgba(148,197,233,0.15),0_12px_40px_-8px_rgba(0,0,0,0.4)] transition-all">
              <ChatInput
                onSubmit={sendMessage}
                onCancel={cancel}
                isLoading={isSending}
                disabled={isLoading}
              />
            </div>
            <p className="mt-1.5 text-center text-[11px] text-muted-foreground/60">
              Enter to send · Shift+Enter for new line
            </p>
          </div>
        </div>
      </div>

      {/* Agent Activity Panel */}
      {showPanel && (isSending || messages.length > 0) && (
        <AgentActivityPanel
          activeAgent={isSending ? "orchestrator" : activeAgent}
          activities={activities}
          handoff={handoffInfo}
          onMinimize={() => setShowPanel(false)}
        />
      )}
    </div>
  );
}
