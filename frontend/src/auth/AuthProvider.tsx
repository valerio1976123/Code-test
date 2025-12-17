/* eslint-disable react-refresh/only-export-components */
import * as React from "react";
import axios from "axios";
import { api } from "../api/client";
import type { User } from "../api/types";

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const AuthContext = React.createContext<AuthContextValue | undefined>(undefined);

function backendUrl(): string {
  const explicit = import.meta.env.VITE_BACKEND_URL as string | undefined;
  if (explicit) return explicit;

  const base = api.defaults.baseURL ?? "http://localhost:8000/api";
  return base.replace(/\/api\/?$/, "");
}

async function ensureCsrfCookie() {
  await axios.get(`${backendUrl()}/sanctum/csrf-cookie`, {
    withCredentials: true,
  });
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  const refresh = React.useCallback(async () => {
    try {
      const res = await api.get<{ user: User }>("/me");
      setUser(res.data.user ?? null);
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void refresh();
  }, [refresh]);

  const login = React.useCallback(async (email: string, password: string) => {
    await ensureCsrfCookie();
    const res = await api.post<{ user: User }>("/login", { email, password });
    setUser(res.data.user);
  }, []);

  const logout = React.useCallback(async () => {
    await api.post("/logout");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

