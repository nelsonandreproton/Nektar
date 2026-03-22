"""MIDI audio output using mido + python-rtmidi (routes to Windows MIDI synth)."""
import mido
import time
import threading
from typing import List, Dict, Optional


class AudioPlayer:
    def __init__(self):
        self._port: Optional[mido.ports.BaseOutput] = None
        self._init_output()

    def get_output_devices(self) -> List[str]:
        try:
            return mido.get_output_names()
        except Exception:
            return []

    def _init_output(self):
        outputs = self.get_output_devices()
        if not outputs:
            return
        # Prefer Windows GS Wavetable Synth on Windows
        preferred = [o for o in outputs if "wavetable" in o.lower() or "microsoft" in o.lower()]
        device = preferred[0] if preferred else outputs[0]
        try:
            self._port = mido.open_output(device)
            # Set channel 0 to Acoustic Grand Piano (program 0)
            self._port.send(mido.Message("program_change", program=0, channel=0))
        except Exception:
            self._port = None

    def note_on(self, note: int, velocity: int = 80, channel: int = 0):
        if self._port and 0 <= note <= 127:
            try:
                self._port.send(mido.Message("note_on", note=note, velocity=velocity, channel=channel))
            except Exception:
                pass

    def note_off(self, note: int, channel: int = 0):
        if self._port and 0 <= note <= 127:
            try:
                self._port.send(mido.Message("note_off", note=note, velocity=0, channel=channel))
            except Exception:
                pass

    def all_notes_off(self):
        if self._port:
            for note in range(128):
                try:
                    self._port.send(mido.Message("note_off", note=note, velocity=0))
                except Exception:
                    pass

    def play_sequence(
        self,
        notes: List[Dict],
        bpm: float,
        on_note_cb=None,
        stop_event: Optional[threading.Event] = None,
    ):
        """
        Play a list of note dicts [{note, beat, duration, velocity?}] at given BPM.
        Calls on_note_cb(note, is_on) for each event if provided.
        """
        beat_duration = 60.0 / bpm

        events: List = []
        for n in notes:
            start = n["beat"] * beat_duration
            end = (n["beat"] + n.get("duration", 1.0)) * beat_duration
            vel = n.get("velocity", 80)
            events.append((start, True, n["note"], vel))
            events.append((end, False, n["note"], 0))

        events.sort(key=lambda x: x[0])

        start_time = time.monotonic()
        for event_time, is_on, note, velocity in events:
            if stop_event and stop_event.is_set():
                break
            wait = event_time - (time.monotonic() - start_time)
            if wait > 0:
                if stop_event:
                    stop_event.wait(timeout=wait)
                    if stop_event.is_set():
                        break
                else:
                    time.sleep(wait)

            if is_on:
                self.note_on(note, velocity)
            else:
                self.note_off(note)
            if on_note_cb:
                on_note_cb(note, is_on)

        self.all_notes_off()

    def close(self):
        if self._port:
            self.all_notes_off()
            self._port.close()
            self._port = None
