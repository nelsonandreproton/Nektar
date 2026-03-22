/**
 * WebSocket client — single persistent connection to the Python backend.
 * Dispatches received messages as custom DOM events on `window`.
 */
const WS_URL = "ws://localhost:8765";

const WS = (() => {
  let socket = null;
  let reconnectTimer = null;
  const RECONNECT_DELAY = 2000;

  function connect() {
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      console.log("[WS] connected");
      window.dispatchEvent(new CustomEvent("ws:open"));
    };

    socket.onclose = () => {
      console.log("[WS] disconnected — retrying in", RECONNECT_DELAY, "ms");
      window.dispatchEvent(new CustomEvent("ws:close"));
      reconnectTimer = setTimeout(connect, RECONNECT_DELAY);
    };

    socket.onerror = (err) => {
      console.warn("[WS] error", err);
    };

    socket.onmessage = (event) => {
      let msg;
      try {
        msg = JSON.parse(event.data);
      } catch {
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
