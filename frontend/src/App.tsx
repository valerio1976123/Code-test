import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider, useAuth } from "./auth/AuthProvider";
import { AppShell } from "./layout/AppShell";
import { DashboardPage } from "./pages/Dashboard";
import { DevicesPage } from "./pages/Devices";
import { ExecutionDetailPage } from "./pages/ExecutionDetail";
import { HistoryPage } from "./pages/History";
import { LoginPage } from "./pages/Login";
import { SchedulesPage } from "./pages/Schedules";

function RequireAuth({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="p-6 text-sm text-slate-600">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function LoginGate() {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="p-6 text-sm text-slate-600">Loading…</div>;
  if (user) return <Navigate to="/" replace />;
  return <LoginPage />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginGate />} />

          <Route
            path="/"
            element={
              <RequireAuth>
                <AppShell />
              </RequireAuth>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="devices" element={<DevicesPage />} />
            <Route path="schedules" element={<SchedulesPage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="executions/:id" element={<ExecutionDetailPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster richColors position="top-right" />
    </AuthProvider>
  );
}
