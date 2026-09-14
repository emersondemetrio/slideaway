import { io } from "socket.io-client";
import { API_URL } from "./api.js";

let socket = null;

export function connectSocket() {
  if (!socket) {
    socket = io(API_URL, { transports: ["websocket"] });
  }
  return socket;
}

export function joinRoom(roomId) {
  connectSocket().emit("join_room", { room_id: roomId });
}

export function leaveRoom(roomId) {
  connectSocket().emit("leave_room", { room_id: roomId });
}

export function onSlideChanged(callback) {
  connectSocket().on("slide_changed", callback);
}

export function onPresentationEnded(callback) {
  connectSocket().on("presentation_ended", callback);
}

export function onReaction(callback) {
  connectSocket().on("reaction", callback);
}
