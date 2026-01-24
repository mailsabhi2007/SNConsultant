import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";
import { useTheme } from "./hooks/useTheme";
import { AppShell } from "./components/layout/AppShell";
import { LoadingScreen } from "./components/common/LoadingSpinner";
import { ROUTES } from "./lib/constants";

// Lazy load pages for code splitting
const LoginPage = lazy(() =>
  import("./pages/Login").then((m) => ({ default: m.LoginPage }))
);
const ChatPage = lazy(() =>
  import("./pages/Chat").then((m) => ({ default: m.ChatPage }))
);
const KnowledgeBasePage = lazy(() =>
  import("./pages/KnowledgeBase").then((m) => ({ default: m.KnowledgeBasePage }))
);
const SettingsPage = lazy(() =>
  import("./pages/Settings").then((m) => ({ default: m.SettingsPage }))
);
const AdminPage = lazy(() =>
  import("./pages/Admin").then((m) => ({ default: m.AdminPage }))
);

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  if (!user) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  return <AppShell>{children}</AppShell>;
}

export default function App() {
  const { user, isLoading } = useAuth();

  // Initialize theme
  useTheme();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <Suspense fallback={<LoadingScreen />}>
      <Routes>
        {/* Public routes */}
        <Route
          path={ROUTES.LOGIN}
          element={user ? <Navigate to={ROUTES.CHAT} replace /> : <LoginPage />}
        />

        {/* Redirect root to chat or login */}
        <Route
          path={ROUTES.HOME}
          element={
            user ? (
              <Navigate to={ROUTES.CHAT} replace />
            ) : (
              <Navigate to={ROUTES.LOGIN} replace />
            )
          }
        />

        {/* Protected routes */}
        <Route
          path={ROUTES.CHAT}
          element={
            <ProtectedRoute>
              <ChatPage />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.KNOWLEDGE_BASE}
          element={
            <ProtectedRoute>
              <KnowledgeBasePage />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.SETTINGS}
          element={
            <ProtectedRoute>
              <SettingsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path={ROUTES.ADMIN}
          element={
            <ProtectedRoute>
              <AdminPage />
            </ProtectedRoute>
          }
        />

        {/* Catch all - redirect to home */}
        <Route path="*" element={<Navigate to={ROUTES.HOME} replace />} />
      </Routes>
    </Suspense>
  );
}
