"""WebSocket server: glues MIDI input, lesson engine, and audio player together."""
import asyncio
import base64
import json
import logging
import threading
from typing import Set

import websockets
from websockets.server import WebSocketServerProtocol

from .midi_handler import MidiHandler
from .audio_player import AudioPlayer
from .lesson_engine import LessonEngine
from .lessons_library import get_lesson_by_id, get_lessons_summary
from .midi_parser import parse_midi_from_bytes

log = logging.getLogger(__name__)

# Input constraints
_MAX_CLIENTS    = 8
_MAX_MSG_BYTES  = 15 * 1024 * 1024   # 15 MB (covers base64-encoded 10 MB MIDI)
_MAX_B64_BYTES  = 14 * 1024 * 1024   # base64 payload limit
_VALID_HANDS    = frozenset({"right", "left", "both"})
_VALID_MODES    = frozenset({"wait", "metronome"})
_MAX_NAME_LEN   = 256
_MAX_ID_LEN     = 128


def _str(msg: dict, key: str, default: str = "", maxlen: int = _MAX_NAME_LEN) -> str:
    val = msg.get(key, default)
    return str(val)[:maxlen] if isinstance(val, str) else default


def _num(msg: dict, key: str, default: float, lo: float, hi: float) -> float:
    val = msg.get(key, default)
    try:
        return max(lo, min(float(val), hi))
    except (TypeError, ValueError):
        return default


class PianoServer:
    def __init__(self):
        self.clients: Set[WebSocketServerProtocol] = set()
        self.midi = MidiHandler()
        self.audio = AudioPlayer()
        self.engine = LessonEngine()
        self._loop: asyncio.AbstractEventLoop = None
        self._playback_stop: threading.Event = threading.Event()
        self._playback_thread: threading.Thread = None

        self.engine.set_callbacks(
            on_step_changed=self._sync_broadcast_state,
            on_complete=self._sync_on_complete,
        )

    # ── WebSocket lifecycle ───────────────────────────────────────────────────

    async def handler(self, websocket: WebSocketServerProtocol):
        if len(self.clients) >= _MAX_CLIENTS:
            await websocket.close(1013, "Server full")
            return

        self.clients.add(websocket)
        try:
            async for raw in websocket:
                if len(raw) > _MAX_MSG_BYTES:
                    await websocket.send(json.dumps({"type": "error", "message": "Message too large"}))
                    continue
                try:
                    msg = json.loads(raw)
                    if not isinstance(msg, dict):
                        continue
                except json.JSONDecodeError:
                    continue
                try:
                    await self._handle(websocket, msg)
                except Exception as exc:
                    log.exception("Error handling message type=%s: %s", msg.get("type"), exc)
                    try:
                        await websocket.send(json.dumps({"type": "error", "message": "Internal server error"}))
                    except Exception:
                        pass
        finally:
            self.clients.discard(websocket)

    async def _broadcast(self, payload: dict):
        if not self.clients:
            return
        data = json.dumps(payload)
        results = await asyncio.gather(
            *[c.send(data) for c in list(self.clients)],
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, Exception):
                log.debug("Broadcast to client failed: %s", r)

    def _sync_broadcast_state(self, *_):
        """Thread-safe: schedule a state broadcast from a non-async context."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._broadcast({"type": "lesson_state", "state": self.engine.get_state()}),
                self._loop,
            )

    def _sync_on_complete(self, score: dict):
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._broadcast({"type": "lesson_complete", "score": score}),
                self._loop,
            )

    # ── Message routing ───────────────────────────────────────────────────────

    async def _handle(self, ws: WebSocketServerProtocol, msg: dict):
        t = msg.get("type")
        if not isinstance(t, str):
            return

        if t == "get_devices":
            await ws.send(json.dumps({
                "type": "devices",
                "inputs": self.midi.get_input_devices(),
                "outputs": self.audio.get_output_devices(),
            }))

        elif t == "connect_device":
            name = _str(msg, "name")
            ok = self.midi.connect(name, self._midi_callback)
            await self._broadcast({
                "type": "device_connected" if ok else "error",
                "name": name,
                "message": None if ok else f"Could not connect to '{name}'",
            })

        elif t == "disconnect_device":
            self.midi.disconnect()
            await self._broadcast({"type": "device_disconnected"})

        elif t == "get_lessons":
            await ws.send(json.dumps({"type": "lessons", "lessons": get_lessons_summary()}))

        elif t == "start_lesson":
            lesson_id = _str(msg, "lesson_id", maxlen=_MAX_ID_LEN)
            lesson = get_lesson_by_id(lesson_id)
            if not lesson:
                await ws.send(json.dumps({"type": "error", "message": "Lesson not found"}))
                return
            self._stop_playback()
            self.engine.load_lesson(lesson)
            hand = _str(msg, "hand")
            if hand in _VALID_HANDS:
                self.engine.set_hand(hand)
            self.engine.start()
            await self._broadcast({"type": "lesson_state", "state": self.engine.get_state()})

        elif t == "stop_lesson":
            self._stop_playback()
            self.engine.stop()
            self.audio.all_notes_off()
            await self._broadcast({"type": "lesson_state", "state": self.engine.get_state()})

        elif t == "set_bpm":
            bpm = _num(msg, "bpm", 60, 20, 240)
            self.engine.set_bpm(bpm)
            await self._broadcast({"type": "lesson_state", "state": self.engine.get_state()})

        elif t == "set_hand":
            hand = _str(msg, "hand")
            if hand in _VALID_HANDS:
                self.engine.set_hand(hand)
                await self._broadcast({"type": "lesson_state", "state": self.engine.get_state()})

        elif t == "set_mode":
            mode = _str(msg, "mode")
            if mode in _VALID_MODES:
                self.engine.set_mode(mode)
                await self._broadcast({"type": "lesson_state", "state": self.engine.get_state()})

        elif t == "play_reference":
            state = self.engine.get_state()
            hand = _str(msg, "hand") or state.get("hand", "right")
            if hand not in _VALID_HANDS:
                hand = "right"
            bpm = _num(msg, "bpm", state.get("bpm", 60), 20, 240)
            notes = self.engine.get_notes_for_hand(hand)
            self._start_playback(notes, bpm)

        elif t == "stop_reference":
            self._stop_playback()
            self.audio.all_notes_off()

        elif t == "load_midi":
            raw_b64 = msg.get("content", "")
            if not isinstance(raw_b64, str):
                await ws.send(json.dumps({"type": "error", "message": "Invalid MIDI content"}))
                return
            if len(raw_b64) > _MAX_B64_BYTES:
                await ws.send(json.dumps({"type": "error", "message": "MIDI file too large"}))
                return
            filename = _str(msg, "filename", "imported.mid", maxlen=120)
            try:
                data = base64.b64decode(raw_b64, validate=True)
                lesson = parse_midi_from_bytes(data, filename)
                self.engine.load_lesson(lesson)
                await self._broadcast({
                    "type": "lesson_loaded",
                    "summary": {
                        "id": lesson["id"],
                        "title": lesson["title"],
                        "category": lesson["category"],
                        "difficulty": lesson["difficulty"],
                        "description": lesson["description"],
                        "hand": lesson.get("hand", "right"),
                    },
                })
            except Exception as exc:
                await ws.send(json.dumps({"type": "error", "message": str(exc)}))

    # ── MIDI input ────────────────────────────────────────────────────────────

    def _midi_callback(self, msg):
        """Called from MIDI thread; schedules async coroutine on event loop."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._process_midi(msg), self._loop)

    async def _process_midi(self, msg):
        if msg.type == "note_on" and msg.velocity > 0:
            self.audio.note_on(msg.note, msg.velocity)
            result = self.engine.note_pressed(msg.note)
            await self._broadcast({
                "type": "note_on",
                "note": msg.note,
                "velocity": msg.velocity,
                "result": result,
            })
            if result in ("correct", "wrong"):
                await self._broadcast({"type": "lesson_state", "state": self.engine.get_state()})

        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            self.audio.note_off(msg.note)
            self.engine.note_released(msg.note)
            await self._broadcast({"type": "note_off", "note": msg.note})

    # ── Reference playback ────────────────────────────────────────────────────

    def _start_playback(self, notes, bpm):
        self._stop_playback()
        self._playback_stop.clear()

        def _cb(note, is_on):
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._broadcast({
                        "type": "playback_note_on" if is_on else "playback_note_off",
                        "note": note,
                    }),
                    self._loop,
                )

        self._playback_thread = threading.Thread(
            target=self.audio.play_sequence,
            args=(notes, bpm),
            kwargs={"on_note_cb": _cb, "stop_event": self._playback_stop},
            daemon=True,
        )
        self._playback_thread.start()

    def _stop_playback(self):
        self._playback_stop.set()
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=2.0)
        self._playback_stop.clear()

    # ── Start server ──────────────────────────────────────────────────────────

    async def start(self, host: str = "localhost", port: int = 8765):
        self._loop = asyncio.get_running_loop()
        async with websockets.serve(self.handler, host, port):
            print(f"WebSocket server listening on ws://{host}:{port}")
            await asyncio.Future()  # run forever

    def shutdown(self):
        self._stop_playback()
        self.midi.disconnect()
        self.audio.close()
