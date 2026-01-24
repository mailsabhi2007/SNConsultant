import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Copy, Check, ThumbsUp, ThumbsDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface MessageActionsProps {
  content: string;
  visible?: boolean;
}

export function MessageActions({ content, visible = false }: MessageActionsProps) {
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const handleFeedback = (type: "up" | "down") => {
    setFeedback((prev) => (prev === type ? null : type));
    // TODO: Send feedback to backend
  };

  return (
    <div className="h-8">
      <AnimatePresence>
        {visible && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="flex items-center gap-1 px-1"
          >
          <TooltipProvider delayDuration={300}>
            {/* Copy button */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={handleCopy}
                >
                  {copied ? (
                    <Check className="h-3.5 w-3.5 text-success" />
                  ) : (
                    <Copy className="h-3.5 w-3.5 text-muted-foreground" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                {copied ? "Copied!" : "Copy"}
              </TooltipContent>
            </Tooltip>

            {/* Thumbs up */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn(
                    "h-7 w-7",
                    feedback === "up" && "text-success"
                  )}
                  onClick={() => handleFeedback("up")}
                >
                  <ThumbsUp
                    className="h-3.5 w-3.5"
                    fill={feedback === "up" ? "currentColor" : "none"}
                  />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Good response</TooltipContent>
            </Tooltip>

            {/* Thumbs down */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn(
                    "h-7 w-7",
                    feedback === "down" && "text-destructive"
                  )}
                  onClick={() => handleFeedback("down")}
                >
                  <ThumbsDown
                    className="h-3.5 w-3.5"
                    fill={feedback === "down" ? "currentColor" : "none"}
                  />
                </Button>
              </TooltipTrigger>
              <TooltipContent side="bottom">Poor response</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </motion.div>
      )}
    </AnimatePresence>
    </div>
  );
}
