import { Badge } from "@/components/ui/badge";
import { GitBranch, Database, Zap, AlertCircle } from "lucide-react";
import { motion } from "framer-motion";

interface SystemStatusBarProps {
  multiAgentEnabled?: boolean;
  instanceConnected?: boolean;
}

export function SystemStatusBar({ multiAgentEnabled = false, instanceConnected = false }: SystemStatusBarProps) {
  if (!multiAgentEnabled && !instanceConnected) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="border-b bg-muted/30 px-4 py-2"
    >
      <div className="mx-auto max-w-3xl flex items-center justify-between">
        <div className="flex items-center gap-3">
          {multiAgentEnabled && (
            <Badge variant="outline" className="bg-blue-50 border-blue-200 text-blue-700 flex items-center gap-1.5">
              <GitBranch className="h-3 w-3" />
              <span className="font-medium">Multi-Agent System</span>
              <motion.div
                className="h-1.5 w-1.5 rounded-full bg-green-500"
                animate={{ opacity: [1, 0.5, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </Badge>
          )}

          {instanceConnected && (
            <Badge variant="outline" className="bg-green-50 border-green-200 text-green-700 flex items-center gap-1.5">
              <Database className="h-3 w-3" />
              <span className="font-medium">Instance Connected</span>
              <Zap className="h-3 w-3 text-green-600" />
            </Badge>
          )}
        </div>

        <div className="text-xs text-muted-foreground flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          <span>Intelligent routing active</span>
        </div>
      </div>
    </motion.div>
  );
}
