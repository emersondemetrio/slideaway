import { beforeEach, describe, expect, it } from "vitest";
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  getRole,
  hasRole,
  isAuthenticated,
  setTokens,
} from "./auth.js";

function fakeJwt(payload) {
  const base64url = (obj) =>
    btoa(JSON.stringify(obj)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  return `${base64url({ alg: "none" })}.${base64url(payload)}.signature`;
}

beforeEach(() => {
  localStorage.clear();
});

describe("token storage", () => {
  it("starts with no tokens", () => {
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
    expect(isAuthenticated()).toBe(false);
  });

  it("stores and retrieves both tokens", () => {
    setTokens("access-123", "refresh-456");
    expect(getAccessToken()).toBe("access-123");
    expect(getRefreshToken()).toBe("refresh-456");
    expect(isAuthenticated()).toBe(true);
  });

  it("clears both tokens", () => {
    setTokens("access-123", "refresh-456");
    clearTokens();
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
    expect(isAuthenticated()).toBe(false);
  });
});

describe("getRole", () => {
  it("returns null when there is no token", () => {
    expect(getRole()).toBeNull();
  });

  it("returns null for a malformed token instead of throwing", () => {
    setTokens("not-a-real-jwt", "refresh-456");
    expect(getRole()).toBeNull();
  });

  it("decodes the role claim from a valid token", () => {
    setTokens(fakeJwt({ role: "super_admin" }), "refresh-456");
    expect(getRole()).toBe("super_admin");
  });
});

describe("hasRole", () => {
  it("returns false when not authenticated", () => {
    expect(hasRole("user")).toBe(false);
  });

  it("a user role does not satisfy a super_admin requirement", () => {
    setTokens(fakeJwt({ role: "user" }), "refresh-456");
    expect(hasRole("super_admin")).toBe(false);
  });

  it("a super_admin role satisfies a user requirement", () => {
    setTokens(fakeJwt({ role: "super_admin" }), "refresh-456");
    expect(hasRole("user")).toBe(true);
  });

  it("a matching role satisfies its own requirement", () => {
    setTokens(fakeJwt({ role: "user" }), "refresh-456");
    expect(hasRole("user")).toBe(true);
  });
});
