# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
# Install dependencies (Windows)
setup.bat
# or manually:
pip install mido python-rtmidi websockets

# Start the app
python main.py
```

This opens `http://localhost:8080` in the browser and connects the WebSocket backend on port 8765.

## Architecture

```
main.py                     Entry point: starts HTTP server (port 8080) + WebSocket server (port 8765)
backend/
  websocket_server.py       PianoServer class — routes all messages between MIDI, engine, and audio
  midi_handler.py           Wraps mido/python-rtmidi; polls MIDI input in a background thread
  audio_player.py           Sends note_on/note_off to Windows MIDI synth via mido output port
  lesson_engine.py          State machine: tracks expected notes, scores input, advances steps
  lessons_library.py        All built-in lessons (scales, chords, exercises, songs) as Python dicts
  midi_parser.py            Parses raw MIDI bytes into the lesson dict format
frontend/
  index.html                Single-page app shell
  css/style.css             Dark piano theme, all layout
  js/websocket.js           WS client — re-dispatches messages as DOM CustomEvents (ws:<type>)
  js/keyboard.js            Renders 61-key virtual keyboard (CSS divs); exposes setState/setExpected
  js/lesson.js              Lesson list rendering, hint chips, score bar
  js/app.js                 Main controller: wires DOM events ↔ WebSocket sends
```

## Key data contracts

### Lesson dict format
```python
{
  "id": "scales/c_major_rh",
  "title": "...", "category": "scales|chords|songs|exercises",
  "difficulty": 1-5, "description": "...",
  "default_bpm": 60, "hand": "right|left|both",

  # Single-hand lessons:
  "notes": [{"note": 60, "beat": 0.0, "duration": 1.0, "hand": "right", "velocity": 80}],

  # Two-hand lessons (use "tracks" instead of "notes"):
  "tracks": {"right": [...], "left": [...]}
}
```

Notes at the same `beat` value are grouped into a single chord step by `LessonEngine._build_steps()`.

### WebSocket messages (server → browser)
| type | key fields |
|---|---|
| `devices` | `inputs`, `outputs` |
| `device_connected` | `name` |
| `note_on` | `note`, `velocity`, `result` (`correct`\|`wrong`\|`unexpected`) |
| `note_off` | `note` |
| `lesson_state` | `state` (see `LessonEngine.get_state()`) |
| `lesson_complete` | `score` |
| `playback_note_on/off` | `note` |
| `lesson_loaded` | `summary` (no note data) |
| `error` | `message` |

### WebSocket messages (browser → server)
`get_devices`, `connect_device`, `get_lessons`, `start_lesson`, `stop_lesson`, `set_bpm`, `set_hand`, `set_mode`, `play_reference`, `stop_reference`, `load_midi`

## Thread safety
The MIDI callback runs in a background thread. All WebSocket sends from non-async contexts use `asyncio.run_coroutine_threadsafe(coro, self._loop)`. Never call `await` directly from `MidiHandler._listen_loop`.

## Adding lessons
Add entries to the `LESSONS` list in `backend/lessons_library.py`. The lesson is automatically included in the sidebar and the `_LESSON_MAP` dict. No other changes needed.
