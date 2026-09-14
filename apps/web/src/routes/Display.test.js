import { render, screen } from "@testing-library/svelte";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Display from "./Display.svelte";

const { apiFetchMock } = vi.hoisted(() => ({ apiFetchMock: vi.fn() }));
vi.mock("../lib/api.js", () => ({ apiFetch: apiFetchMock }));

const { joinRoomMock, leaveRoomMock, onSlideChangedMock, onPresentationEndedMock, onReactionMock } =
  vi.hoisted(() => ({
    joinRoomMock: vi.fn(),
    leaveRoomMock: vi.fn(),
    onSlideChangedMock: vi.fn(),
    onPresentationEndedMock: vi.fn(),
    onReactionMock: vi.fn(),
  }));
vi.mock("../lib/socket.js", () => ({
  joinRoom: joinRoomMock,
  leaveRoom: leaveRoomMock,
  onSlideChanged: onSlideChangedMock,
  onPresentationEnded: onPresentationEndedMock,
  onReaction: onReactionMock,
}));

beforeEach(() => {
  apiFetchMock.mockReset();
  joinRoomMock.mockClear();
  leaveRoomMock.mockClear();
  onSlideChangedMock.mockClear();
  onPresentationEndedMock.mockClear();
  onReactionMock.mockClear();
});

describe("Display", () => {
  it("fetches the room's current state on mount", async () => {
    apiFetchMock.mockResolvedValue({
      id: "room-1",
      deck_id: "deck-1",
      status: "active",
      current_slide_index: 0,
    });

    render(Display, { props: { params: { roomId: "room-1" } } });

    expect(await screen.findByText("Slide 1")).toBeInTheDocument();
    expect(apiFetchMock).toHaveBeenCalledWith("/rooms/room-1");
  });

  it("renders the slide the room was already on, not slide 1, when joining mid-presentation", async () => {
    apiFetchMock.mockResolvedValue({
      id: "room-1",
      deck_id: "deck-1",
      status: "active",
      current_slide_index: 6,
    });

    render(Display, { props: { params: { roomId: "room-1" } } });

    expect(await screen.findByText("Slide 7")).toBeInTheDocument();
  });

  it("shows the ended screen immediately if the room already ended before mount", async () => {
    apiFetchMock.mockResolvedValue({
      id: "room-1",
      deck_id: "deck-1",
      status: "ended",
      current_slide_index: 3,
    });

    render(Display, { props: { params: { roomId: "room-1" } } });

    expect(await screen.findByText("Thanks for joining!")).toBeInTheDocument();
  });
});
