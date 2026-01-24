import { useState } from "react";
import { MoreHorizontal, Trash2, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn, formatDate, truncate } from "@/lib/utils";
import type { Conversation } from "@/types";

interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
  isDeleting?: boolean;
}

export function ConversationItem({
  conversation,
  isActive,
  onSelect,
  onDelete,
  isDeleting,
}: ConversationItemProps) {
  const [showMenu, setShowMenu] = useState(false);

  return (
    <button
      onClick={onSelect}
      onMouseEnter={() => setShowMenu(true)}
      onMouseLeave={() => setShowMenu(false)}
      className={cn(
        "group flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors",
        isActive
          ? "bg-accent text-accent-foreground"
          : "hover:bg-accent/50 text-foreground"
      )}
    >
      <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />

      <div className="flex-1 overflow-hidden">
        <p className="truncate font-medium">
          {truncate(conversation.title, 30)}
        </p>
        <p className="text-xs text-muted-foreground">
          {formatDate(conversation.updated_at)}
        </p>
      </div>

      {/* Actions */}
      <div
        className={cn(
          "transition-opacity",
          showMenu ? "opacity-100" : "opacity-0 group-hover:opacity-100"
        )}
      >
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              disabled={isDeleting}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </button>
  );
}
