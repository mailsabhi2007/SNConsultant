import { useEffect, useState } from "react";
import { getMe, login as apiLogin, logout as apiLogout, register as apiRegister } from "../services/auth";
import { useAuthStore } from "../store/authStore";

export function useAuth() {
  const { user, setUser } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    getMe()
      .then((current) => {
        if (isMounted) {
          setUser(current);
        }
      })
      .catch(() => {
        if (isMounted) {
          setUser(null);
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, [setUser]);

  const login = async (username: string, password: string) => {
    const current = await apiLogin(username, password);
    setUser(current);
    return current;
  };

  const register = async (username: string, password: string, email?: string) => {
    const current = await apiRegister(username, password, email);
    setUser(current);
    return current;
  };

  const logout = async () => {
    await apiLogout();
    setUser(null);
  };

  return { user, isLoading, login, register, logout };
}
