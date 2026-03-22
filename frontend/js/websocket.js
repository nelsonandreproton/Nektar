/**
 * WebSocket client — single persistent connection to the Python backend.
 * Dispatches received messages as custom DOM events on `window`.
 * Reconnects with exponential backoff (2 s → 4 s → 8 s … max 30 s).
 */
const WS_URL = "ws://localhost:8765";

const WS = (() => {
  let socket = null;
  let retryDelay = 2000;
  const MAX_DELAY = 30_000;

  function connect() {
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      retryDelay = 2000;  // reset backoff on successful connect
      console.log("[WS] connected");
      window.dispatchEvent(new CustomEvent("ws:open"));
    };

    socket.onclose = () => {
      console.log(`[WS] disconnected — retrying in ${retryDelay / 1000}s`);
      window.dispatchEvent(new CustomEvent("ws:close"));
      setTimeout(connect, retryDelay);
      retryDelay = Math.min(retryDelay * 1.5, MAX_DELAY);
    };

    socket.onerror = (err) => {
      console.warn("[WS] error", err);
      // onclose will fire after onerror, triggering reconnect
    };

    socket.onmessage = (event) => {
      let msg;
      try {
        msg = JSON.parse(event.data);
      } catch {
        console.warn("[WS] received non-JSON message");
        return;
      }
      if (typeof msg.type !== "string") {
        console.warn("[WS] message missing string 'type' field", msg);
        return;
      }
      window.dispatchEvent(new CustomEvent(`ws:${msg.type}`, { detail: msg }));
    };
  }

  function send(obj) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(obj));
    }
  }

  connect();

  return { send };
})();
