# Nektar

A local piano practice app. Connect a MIDI keyboard, pick a lesson, and get real-time note-by-note feedback as you play. Progress is tracked through a structured curriculum with mastery gating and spaced repetition.

![Python](https://img.shields.io/badge/Python-3.12+-blue) ![WebSockets](https://img.shields.io/badge/WebSockets-12.0-green) ![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)

---

## Features

- **Real-time MIDI feedback** — correct, wrong, and unexpected notes highlighted instantly on a virtual keyboard
- **Structured curriculum** — diagnostic assessment places you in the right stage; lessons unlock as you master each one
- **Mastery gating** — 3 consecutive passes at ≥90% accuracy (and minimum BPM where required) to unlock the next lesson
- **Spaced repetition** — mastered lessons resurface for review after 14 days of inactivity
- **Practice vs. Assess modes** — practice freely without affecting progress; assess mode records toward mastery
- **Three play modes** — Wait (advance only on correct input), Drill (reset chord on wrong note), Metronome
- **Loop section** — isolate and repeat any range of steps
- **Auto-speed** — BPM increases automatically after consecutive correct steps
- **Reference playback** — hear the lesson before attempting it
- **Coaching tips** — personalised technique advice in Portuguese after each failed attempt
- **MIDI file import** — load any `.mid` file as a custom lesson
- **Progress export/import** — back up and restore your mastery data as JSON

---

## Requirements

- Python 3.12+
- A MIDI keyboard connected via USB (or any MIDI-capable device)
- Windows (uses the built-in Windows MIDI synth for audio output)

---

## Setup

```bash
pip install mido python-rtmidi websockets
```

Or on Windows, run `setup.bat`.

---

## Running

```bash
python main.py
```

Opens `http://localhost:8080` in the browser automatically. The WebSocket backend runs on `ws://localhost:8765`.

---

## Architecture

```
main.py                     Entry point — HTTP server (port 8080) + WebSocket server (port 8765)
backend/
  websocket_server.py       PianoServer — routes all messages between MIDI, engine, and audio
  lesson_engine.py          State machine — tracks expected notes, scores input, advances steps
  course_engine.py          Curriculum, mastery gating, spaced repetition, progress persistence
  coach.py                  Rule-based coaching tips after failed attempts
  lessons_library.py        Built-in lessons (scales, chords, songs, exercises)
  midi_handler.py           MIDI input — polls device in a background thread
  audio_player.py           MIDI output — sends note_on/note_off to Windows synth
  midi_parser.py            Parses .mid files into the lesson dict format
frontend/
  index.html                Single-page app shell
  css/style.css             Dark piano theme
  js/websocket.js           WS client — re-dispatches messages as DOM CustomEvents
  js/keyboard.js            61-key virtual keyboard
  js/lesson.js              Lesson list, hint chips, score bar
  js/app.js                 Main controller — wires DOM events ↔ WebSocket sends
```

The MIDI callback runs in a background thread. All WebSocket sends from non-async contexts use `asyncio.run_coroutine_threadsafe`.

---

## Adding Lessons

Add entries to the `LESSONS` list in `backend/lessons_library.py`:

```python
{
    "id": "scales/g_major_rh",
    "title": "G Major Scale (Right Hand)",
    "category": "scales",           # scales | chords | songs | exercises
    "difficulty": 2,                # 1–5
    "description": "G major scale, one octave.",
    "default_bpm": 60,
    "hand": "right",                # right | left | both
    "notes": [
        {"note": 67, "beat": 0.0, "duration": 1.0, "hand": "right", "velocity": 80},
        # ...
    ],
}
```

Notes sharing the same `beat` value are grouped into a chord step. For two-hand lessons, use `"tracks": {"right": [...], "left": [...]}` instead of `"notes"`.

---

## Progress Data

Mastery progress is saved to `data/progress.json`. Export/import is available from the UI.
