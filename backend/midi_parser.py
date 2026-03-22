"""Parse MIDI files (bytes) into the app's lesson format."""
import io
import mido
from typing import Optional


def parse_midi_from_bytes(data: bytes, filename: str = "imported.mid") -> dict:
    """
    Parse raw MIDI bytes and return a lesson dict.
    Raises ValueError if no note data is found.
    """
    buf = io.BytesIO(data)
    mid = mido.MidiFile(file=buf)

    ticks_per_beat = mid.ticks_per_beat
    tempo = 500_000  # µs per beat → 120 BPM default

    # Extract tempo from the first track (track 0 is usually meta)
    for msg in mid.tracks[0]:
        if msg.type == "set_tempo":
            tempo = msg.tempo
            break

    bpm = round(60_000_000 / tempo)

    all_tracks = []
    for track_idx, track in enumerate(mid.tracks):
        notes = _extract_notes(track, ticks_per_beat)
        if notes:
            all_tracks.append(notes)

    if not all_tracks:
        raise ValueError("No note data found in MIDI file.")

    title = filename.replace(".mid", "").replace(".midi", "").replace("_", " ").title()

    lesson: dict = {
        "id": f"midi/{filename}",
        "title": title,
        "category": "songs",
        "difficulty": 3,
        "description": f"Imported: {filename}",
        "default_bpm": bpm,
    }

    if len(all_tracks) >= 2:
        lesson["tracks"] = {"right": all_tracks[0], "left": all_tracks[1]}
        lesson["hand"] = "both"
    else:
        lesson["notes"] = all_tracks[0]
        lesson["hand"] = "right"

    return lesson


def _extract_notes(track, ticks_per_beat: int):
    notes = []
    active: dict = {}  # note → (start_beat, velocity)
    tick = 0

    for msg in track:
        tick += msg.time
        beat = tick / ticks_per_beat

        if msg.type == "note_on" and msg.velocity > 0:
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

    return notes
