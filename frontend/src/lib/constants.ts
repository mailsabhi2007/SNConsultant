export const APP_NAME = "ServiceNow Consultant";

export const ROUTES = {
  HOME: "/",
  CHAT: "/chat",
  LOGIN: "/login",
  KNOWLEDGE_BASE: "/knowledge-base",
  SETTINGS: "/settings",
  ADMIN: "/admin",
} as const;

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: "/api/auth/login",
    REGISTER: "/api/auth/register",
    LOGOUT: "/api/auth/logout",
    ME: "/api/auth/me",
  },
  CHAT: {
    SEND: "/api/chat",
    STREAM: "/api/chat/stream",
    CONVERSATIONS: "/api/conversations",
    CONVERSATION: (id: string) => `/api/conversations/${id}`,
  },
  KNOWLEDGE_BASE: {
    FILES: "/api/knowledge-base/files",
    UPLOAD: "/api/knowledge-base/upload",
    DELETE: (fileId: string) => `/api/knowledge-base/files/${fileId}`,
  },
  SETTINGS: {
    GET: "/api/settings",
    UPDATE: "/api/settings",
  },
  ADMIN: {
    STATS: "/api/admin/stats",
  },
} as const;

export const KEYBOARD_SHORTCUTS = {
  COMMAND_PALETTE: ["Meta+k", "Ctrl+k"],
  NEW_CHAT: ["Meta+n", "Ctrl+n"],
  TOGGLE_SIDEBAR: ["Meta+b", "Ctrl+b"],
  FOCUS_INPUT: ["/"],
} as const;

export const MESSAGE_ROLES = {
  USER: "user",
  ASSISTANT: "assistant",
  SYSTEM: "system",
} as const;

export const THEME = {
  LIGHT: "light",
  DARK: "dark",
  SYSTEM: "system",
} as const;
