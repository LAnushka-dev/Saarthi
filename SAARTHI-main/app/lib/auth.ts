// Simple auth helper - stores login state in sessionStorage

export const AUTH_KEY = "saarthi_user";

export type SaarthiUser = {
  id: string;
  name: string;
  phone: string;
  role: "vendor" | "transporter";
};

export function saveUser(user: SaarthiUser) {
  sessionStorage.setItem(AUTH_KEY, JSON.stringify(user));
}

export function getUser(): SaarthiUser | null {
  if (typeof window === "undefined") return null;
  const data = sessionStorage.getItem(AUTH_KEY);
  if (!data) return null;
  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
}

export function logout() {
  sessionStorage.removeItem(AUTH_KEY);
}

export function isLoggedIn(): boolean {
  return getUser() !== null;
}