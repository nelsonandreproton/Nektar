"""WebSocket server: glues MIDI input, lesson engine, and audio player together."""
import asyncio
import base64
import json
import threading
from typing import Set

import websockets
from websockets.server import WebSocketServerProtocol

from .midi_handler import MidiHandler
from .audio_player import AudioPlayer
from .lesson_engine import LessonEngine
from .lessons_library import get_all_lessons, get_lesson_by_id, get_lessons_summary
from .midi_parser import parse_midi_from_bytes


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
        self.clients.add(websocket)
        try:
            async for raw in websocket:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                await self._handle(websocket, msg)
        finally:
            self.clients.discard(websocket)

    async def _broadcast(self, payload: dict):
        if not self.clients:
            return
        data = json.dumps(payload)
        await asyncio.gather(
            *[c.send(data) for c in list(self.clients)],
            return_exceptions=True,
        )

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

        if t == "get_devices":
            await ws.send(json.dumps({
                "type": "devices",
                "inputs": self.midi.get_input_devices(),
                "outputs": self.audio.get_output_devices(),
            }))

        elif t == "connect_device":
            name = msg.get("name", "")
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
            lesson = get_lesson_by_id(msg.get("lesson_id", ""))
            if not lesson:
                await ws.send(json.dumps({"type": "error", "message": "Lesson not found"}))
                return
            self._stop_playback()
            self.engine.load_lesson(lesson)
            if msg.get("hand"):
                self.engine.set_hand(msg["hand"])
            self.engine.start()
            await self._broadcast({"type": "lesson_state", "state": self.engine.get_state()})

        elif t == "stop_lesson":
            self._stop_playback()
            self.engine.stop()
            self.audio.all_notes_off()
            await self._broadcast({"type": "lesson_state", "state": self.engine.get_state()})

        elif t == "set_bpm":
            self.engine.set_bpm(msg.get("bpm", 60))
            await self._broadcast({"type": "lesson_state", "state": self.engine.get_state()})

        elif t == "set_hand":
            self.engine.set_hand(msg.get("hand", "right"))
            await self._broadcast({"type": "lesson_state", "state": self.engine.get_state()})

        elif t == "set_mode":
            self.engine.set_mode(msg.get("mode", "wait"))
            await self._broadcast({"type": "lesson_state", "state": self.engine.get_state()})

        elif t == "play_reference":
            hand = msg.get("hand", self.engine.get_state().get("hand", "right"))
            bpm = msg.get("bpm", self.engine.get_state().get("bpm", 60))
            notes = self.engine.get_notes_for_hand(hand)
            self._start_playback(notes, bpm)

        elif t == "stop_reference":
            self._stop_playback()
            self.audio.all_notes_off()

        elif t == "load_midi":
            raw_b64 = msg.get("content", "")
            filename = msg.get("filename", "imported.mid")
            try:
                data = base64.b64decode(raw_b64)
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
        """Called from MIDI thread; schedules async coroutine."""
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
            self._playback_thread.join(timeout=1.0)
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
