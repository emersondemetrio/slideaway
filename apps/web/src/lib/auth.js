import { jwtDecode } from "jwt-decode";

const ACCESS_KEY = "slideaway_access_token";
const REFRESH_KEY = "slideaway_refresh_token";

export function setTokens(accessToken, refreshToken) {
  localStorage.setItem(ACCESS_KEY, accessToken);
  localStorage.setItem(REFRESH_KEY, refreshToken);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

export function getRole() {
  const token = getAccessToken();
  if (!token) return null;
  try {
    return jwtDecode(token).role;
  } catch {
    return null;
  }
}

export function isAuthenticated() {
  return getAccessToken() !== null;
}

export function hasRole(minimumRole) {
  const rank = { user: 1, super_admin: 2 };
  const role = getRole();
  if (!role) return false;
  return rank[role] >= rank[minimumRole];
}
