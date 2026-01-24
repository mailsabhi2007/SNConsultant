import { motion } from "framer-motion";
import { Bot } from "lucide-react";

export function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex gap-3"
    >
      {/* Avatar */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
        <Bot className="h-4 w-4" />
      </div>

      {/* Typing dots */}
      <div className="flex items-center gap-1 rounded-2xl rounded-tl-sm bg-muted px-4 py-3">
        <TypingDot delay={0} />
        <TypingDot delay={0.2} />
        <TypingDot delay={0.4} />
      </div>
    </motion.div>
  );
}

function TypingDot({ delay }: { delay: number }) {
  return (
    <motion.div
      className="h-2 w-2 rounded-full bg-muted-foreground/40"
      animate={{
        scale: [1, 1.2, 1],
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
