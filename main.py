"""Entry point: starts the HTTP server (frontend) and WebSocket server (backend)."""
import asyncio
import os
import sys
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

HTTP_PORT = 8080
WS_PORT = 8765
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")


class SilentHandler(SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler with suppressed console output."""

    def log_message(self, fmt, *args):
        pass


def run_http_server():
    os.chdir(FRONTEND_DIR)
    server = HTTPServer(("localhost", HTTP_PORT), SilentHandler)
    server.serve_forever()


async def main():
    from backend.websocket_server import PianoServer

    # Start static file server in a background thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    server = PianoServer()

    # Open browser after a short delay so the HTTP server is ready
    async def open_browser():
        await asyncio.sleep(0.5)
        webbrowser.open(f"http://localhost:{HTTP_PORT}")
        print(f"Nektar Piano Lessons → http://localhost:{HTTP_PORT}")

    asyncio.create_task(open_browser())

    try:
        await server.start(port=WS_PORT)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()


if __name__ == "__main__":
    print("Starting Nektar Piano Lessons…")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBye!")
        sys.exit(0)
