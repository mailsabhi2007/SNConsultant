import api from "./api";
import { User } from "../store/authStore";

export async function login(username: string, password: string): Promise<User> {
  const response = await api.post<User>("/api/auth/login", { username, password });
  return response.data;
}

export async function register(username: string, password: string, email: string): Promise<User> {
  const response = await api.post<User>("/api/auth/register", { username, password, email });
  return response.data;
}

export async function getMe(): Promise<User> {
  const response = await api.get<User>("/api/auth/me");
  return response.data;
}

export async function logout(): Promise<void> {
  await api.post("/api/auth/logout");
}
