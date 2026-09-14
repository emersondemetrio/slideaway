import { render, screen } from "@testing-library/svelte";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Login from "./Login.svelte";

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }));
vi.mock("svelte-spa-router", () => ({ push: pushMock }));

const { apiFetchMock } = vi.hoisted(() => ({ apiFetchMock: vi.fn() }));
vi.mock("../lib/api.js", () => ({ apiFetch: apiFetchMock }));

const { setTokensMock } = vi.hoisted(() => ({ setTokensMock: vi.fn() }));
vi.mock("../lib/auth.js", () => ({ setTokens: setTokensMock }));

beforeEach(() => {
  pushMock.mockClear();
  apiFetchMock.mockClear();
  setTokensMock.mockClear();
});

describe("Login", () => {
  it("logs in and navigates to the dashboard on success", async () => {
    apiFetchMock.mockResolvedValue({ access_token: "a", refresh_token: "b" });
    const user = userEvent.setup();
    render(Login);

    await user.type(screen.getByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "correct-password");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(apiFetchMock).toHaveBeenCalledWith(
      "/auth/login",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "user@example.com", password: "correct-password" }),
      })
    );
    expect(setTokensMock).toHaveBeenCalledWith("a", "b");
    expect(pushMock).toHaveBeenCalledWith("/dashboard");
  });

  it("shows an error message and does not navigate on failure", async () => {
    apiFetchMock.mockRejectedValue(new Error("Invalid credentials"));
    const user = userEvent.setup();
    render(Login);

    await user.type(screen.getByLabelText("Email"), "user@example.com");
    await user.type(screen.getByLabelText("Password"), "wrong-password");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByText("Invalid credentials")).toBeInTheDocument();
    expect(pushMock).not.toHaveBeenCalled();
  });
});
