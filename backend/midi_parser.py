"""Parse MIDI files (bytes) into the app's lesson format."""
import io
import mido
from typing import Optional

MAX_FILE_BYTES = 10 * 1024 * 1024   # 10 MB
MAX_TRACKS     = 32
MAX_NOTES      = 50_000             # per track


def parse_midi_from_bytes(data: bytes, filename: str = "imported.mid") -> dict:
    """
    Parse raw MIDI bytes and return a lesson dict.
    Raises ValueError if the file is invalid, too large, or has no note data.
    """
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(f"MIDI file too large ({len(data) // 1024} KB). Max is {MAX_FILE_BYTES // 1024} KB.")

    # Sanitise filename (no path components, printable ASCII only)
    safe_name = "".join(c for c in filename if c.isalnum() or c in " ._-")[:80] or "imported.mid"

    try:
        buf = io.BytesIO(data)
        mid = mido.MidiFile(file=buf)
    except Exception as exc:
        raise ValueError(f"Could not parse MIDI file: {exc}") from exc

    if not mid.tracks:
        raise ValueError("MIDI file has no tracks.")

    ticks_per_beat = mid.ticks_per_beat or 480
    tempo = 500_000  # µs per beat → 120 BPM default

    # Extract tempo from the first track (track 0 is usually meta)
    for msg in mid.tracks[0]:
        if msg.type == "set_tempo":
            tempo = max(1, msg.tempo)  # guard against zero division
            break

    bpm = round(60_000_000 / tempo)

    # Process at most MAX_TRACKS tracks to prevent memory exhaustion
    all_tracks = []
    for track in mid.tracks[:MAX_TRACKS]:
        notes = _extract_notes(track, ticks_per_beat)
        if notes:
            all_tracks.append(notes)

    if not all_tracks:
        raise ValueError("No note data found in MIDI file.")

    title = safe_name.replace(".mid", "").replace(".midi", "").replace("_", " ").title()

    lesson: dict = {
        "id": f"midi/{safe_name}",
        "title": title,
        "category": "songs",
        "difficulty": 3,
        "description": f"Imported: {safe_name}",
        "default_bpm": bpm,
    }

    if len(all_tracks) >= 2:
        lesson["tracks"] = {"right": all_tracks[0], "left": all_tracks[1]}
        lesson["hand"] = "both"
    else:
        lesson["notes"] = all_tracks[0]
        lesson["hand"] = "right"

    return lesson


def _extract_notes(track, ticks_per_beat: int) -> list:
    notes = []
    active: dict = {}  # note → (start_beat, velocity)
    tick = 0
    count = 0

    for msg in track:
        tick += msg.time
        beat = tick / ticks_per_beat

        if msg.type == "note_on" and msg.velocity > 0:
            if 0 <= msg.note <= 127:
                active[msg.note] = (beat, msg.velocity)

        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            if msg.note in active:
                start_beat, velocity = active.pop(msg.note)
                duration = beat - start_beat
                notes.append({
                    "note": msg.note,
                    "beat": round(start_beat, 4),
                    "duration": round(max(duration, 0.1), 4),
                    "velocity": velocity,
                })
                count += 1
                if count >= MAX_NOTES:
                    break  # truncate runaway files

    # Force-close any hanging note-on events (malformed MIDI)
    for note, (start_beat, velocity) in active.items():
        notes.append({
            "note": note,
            "beat": round(start_beat, 4),
            "duration": 0.5,
            "velocity": velocity,
        })

    return notes
