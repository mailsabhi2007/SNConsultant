import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSubmit: (message: string) => void;
  onCancel?: () => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSubmit,
  onCancel,
  isLoading = false,
  disabled = false,
  placeholder = "Ask about ServiceNow...",
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [message]);

  // Focus on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const handleSubmit = () => {
    const trimmed = message.trim();
    if (trimmed && !isLoading && !disabled) {
      onSubmit(trimmed);
      setMessage("");
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter (without Shift)
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const canSubmit = message.trim().length > 0 && !isLoading && !disabled;

  return (
    <div className="relative">
      <div
        className={cn(
          "flex items-end gap-2 rounded-2xl border bg-background p-2 shadow-sm transition-all",
          "focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20",
          disabled && "opacity-50"
        )}
      >
        <Textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isLoading || disabled}
          className={cn(
            "min-h-[44px] max-h-[200px] resize-none border-0 bg-transparent p-2",
            "focus-visible:ring-0 focus-visible:ring-offset-0",
            "placeholder:text-muted-foreground"
          )}
          rows={1}
        />

        <AnimatePresence mode="wait">
          {isLoading ? (
            <motion.div
              key="loading"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 0.1 }}
            >
              <Button
                type="button"
                size="icon"
                variant="ghost"
                onClick={onCancel}
                className="h-9 w-9 shrink-0 text-destructive hover:bg-destructive/10"
              >
                <Square className="h-4 w-4" fill="currentColor" />
              </Button>
            </motion.div>
          ) : (
            <motion.div
              key="send"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 0.1 }}
            >
              <Button
                type="button"
                size="icon"
                onClick={handleSubmit}
                disabled={!canSubmit}
                className={cn(
                  "h-9 w-9 shrink-0 rounded-xl transition-all",
                  canSubmit
                    ? "bg-primary text-primary-foreground hover:bg-primary/90"
                    : "bg-muted text-muted-foreground"
                )}
              >
                <Send className="h-4 w-4" />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Keyboard shortcut hint */}
      <p className="mt-2 text-center text-xs text-muted-foreground">
        Press <kbd className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">Enter</kbd> to send,{" "}
        <kbd className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">Shift+Enter</kbd> for new line
      </p>
    </div>
  );
}
