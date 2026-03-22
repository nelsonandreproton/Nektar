"""Lesson state machine: tracks expected notes, scores input, manages progression."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Callable


@dataclass
class LessonStep:
    notes: Set[int]
    beat: float
    duration: float
    hand: str = "right"
    fingering: Dict[int, int] = field(default_factory=dict)  # midi → finger (1-5)


class LessonEngine:
    def __init__(self):
        self._lesson: Optional[dict] = None
        self._steps: List[LessonStep] = []
        self._current_step: int = 0
        self._pressed_this_step: Set[int] = set()
        self._wrong_notes: Set[int] = set()
        self._status: str = "idle"  # idle | playing | completed
        self._hand: str = "right"
        self._mode: str = "wait"  # wait | drill | metronome
        self._bpm: float = 60.0
        self._score: dict = {"correct": 0, "wrong": 0, "missed": 0, "total": 0}

        # Auto-speed (adaptive BPM)
        self._auto_speed: bool = False
        self._auto_speed_streak: int = 0
        self._auto_speed_threshold: int = 5   # consecutive correct steps before BPM bump
        self._auto_speed_step: float = 5.0    # BPM increment per threshold hit
        self._auto_speed_max: float = 200.0

        # Loop section
        self._loop_start: Optional[int] = None
        self._loop_end: Optional[int] = None

        self._on_step_changed: Optional[Callable] = None
        self._on_note_result: Optional[Callable] = None
        self._on_complete: Optional[Callable] = None

    def set_callbacks(self, on_step_changed=None, on_note_result=None, on_complete=None):
        self._on_step_changed = on_step_changed
        self._on_note_result = on_note_result
        self._on_complete = on_complete

    # ── Loading ──────────────────────────────────────────────────────────────

    def load_lesson(self, lesson: dict):
        self._lesson = lesson
        self._status = "idle"
        self._current_step = 0
        self._pressed_this_step = set()
        self._wrong_notes = set()
        self._bpm = float(lesson.get("default_bpm", 60))
        self._loop_start = None
        self._loop_end = None
        self._auto_speed_streak = 0
        self._build_steps()

    def _build_steps(self):
        if not self._lesson:
            self._steps = []
            return

        raw_notes = self._get_raw_notes()
        beat_groups: Dict[float, Set[int]] = {}
        beat_duration: Dict[float, float] = {}
        beat_hand: Dict[float, str] = {}
        beat_fingering: Dict[float, Dict[int, int]] = {}

        for n in raw_notes:
            beat = round(float(n["beat"]), 4)
            if beat not in beat_groups:
                beat_groups[beat] = set()
                beat_duration[beat] = float(n.get("duration", 1.0))
                beat_hand[beat] = n.get("hand", "right")
                beat_fingering[beat] = {}
            note_num = int(n["note"])
            beat_groups[beat].add(note_num)
            finger = n.get("finger")
            if finger is not None:
                beat_fingering[beat][note_num] = int(finger)

        self._steps = [
            LessonStep(
                notes=beat_groups[b],
                beat=b,
                duration=beat_duration[b],
                hand=beat_hand[b],
                fingering=beat_fingering[b],
            )
            for b in sorted(beat_groups)
        ]
        self._score["total"] = len(self._steps)

    def _get_raw_notes(self) -> List[dict]:
        if not self._lesson:
            return []
        hand = self._hand
        if "tracks" in self._lesson:
            if hand == "right":
                return self._lesson["tracks"].get("right", [])
            elif hand == "left":
                return self._lesson["tracks"].get("left", [])
            else:  # both
                return (
                    self._lesson["tracks"].get("right", [])
                    + self._lesson["tracks"].get("left", [])
                )
        return self._lesson.get("notes", [])

    def get_notes_for_hand(self, hand: str) -> List[dict]:
        """Return flat note list for the given hand (used by audio playback)."""
        saved = self._hand
        self._hand = hand
        notes = self._get_raw_notes()
        self._hand = saved
        return notes

    # ── Control ───────────────────────────────────────────────────────────────

    def start(self):
        self._current_step = 0
        self._pressed_this_step = set()
        self._wrong_notes = set()
        self._auto_speed_streak = 0
        self._score = {"correct": 0, "wrong": 0, "missed": 0, "total": len(self._steps)}
        self._status = "playing"

    def stop(self):
        self._status = "idle"
        self._pressed_this_step = set()
        self._wrong_notes = set()
        self._auto_speed_streak = 0

    def set_hand(self, hand: str):
        if hand not in ("right", "left", "both"):
            raise ValueError(f"Invalid hand: {hand!r}")
        self._hand = hand
        if self._lesson:
            self._build_steps()

    def set_bpm(self, bpm: float):
        if not isinstance(bpm, (int, float)):
            raise ValueError("BPM must be numeric")
        self._bpm = max(20.0, min(float(bpm), 240.0))
        self._auto_speed_streak = 0  # reset streak on manual BPM change

    def set_mode(self, mode: str):
        if mode not in ("wait", "drill", "metronome"):
            raise ValueError(f"Invalid mode: {mode!r}")
        self._mode = mode

    def set_auto_speed(self, enabled: bool):
        self._auto_speed = bool(enabled)
        if not enabled:
            self._auto_speed_streak = 0

    def set_loop(self, start: int, end: int):
        total = len(self._steps)
        if 0 <= start < end <= total:
            self._loop_start = start
            self._loop_end = end

    def clear_loop(self):
        self._loop_start = None
        self._loop_end = None

    # ── Input processing ──────────────────────────────────────────────────────

    def note_pressed(self, note: int) -> str:
        """
        Call when user presses a key.
        Returns: 'correct' | 'wrong' | 'unexpected'
        """
        if self._status != "playing" or self._current_step >= len(self._steps):
            return "unexpected"

        expected = self._steps[self._current_step].notes

        if note in expected:
            self._pressed_this_step.add(note)
            if expected.issubset(self._pressed_this_step):
                self._score["correct"] += 1
                self._auto_speed_streak += 1
                self._check_auto_speed()
                self._advance_step()
            return "correct"
        else:
            if self._mode == "drill":
                # Drill mode: wrong note resets chord attempt, no score penalty
                self._pressed_this_step = set()
            else:
                if note not in self._wrong_notes:
                    self._wrong_notes.add(note)
                    self._score["wrong"] += 1
                    self._auto_speed_streak = 0
            return "wrong"

    def note_released(self, note: int):
        self._pressed_this_step.discard(note)

    def _check_auto_speed(self):
        if not self._auto_speed:
            return
        if self._auto_speed_streak > 0 and self._auto_speed_streak % self._auto_speed_threshold == 0:
            new_bpm = min(self._bpm + self._auto_speed_step, self._auto_speed_max)
            if new_bpm != self._bpm:
                self._bpm = new_bpm

    def _advance_step(self):
        self._current_step += 1
        self._pressed_this_step = set()
        self._wrong_notes = set()

        # Loop section check
        if self._loop_end is not None and self._current_step >= self._loop_end:
            self._current_step = self._loop_start if self._loop_start is not None else 0
            if self._on_step_changed:
                self._on_step_changed(self._current_step)
            return

        if self._current_step >= len(self._steps):
            self._status = "completed"
            if self._on_complete:
                self._on_complete(self._score)
        else:
            if self._on_step_changed:
                self._on_step_changed(self._current_step)

    # ── State serialization ───────────────────────────────────────────────────

    def get_state(self) -> dict:
        current_expected = None
        next_notes = []
        current_fingering = {}

        if self._status == "playing" and self._current_step < len(self._steps):
            step = self._steps[self._current_step]
            current_expected = list(step.notes)
            current_fingering = {str(k): v for k, v in step.fingering.items()}

        if self._current_step + 1 < len(self._steps):
            next_notes = list(self._steps[self._current_step + 1].notes)

        return {
            "status": self._status,
            "lesson": (
                {"id": self._lesson.get("id"), "title": self._lesson.get("title")}
                if self._lesson
                else None
            ),
            "current_step": self._current_step,
            "total_steps": len(self._steps),
            "current_expected": current_expected,
            "current_fingering": current_fingering,
            "next_notes": next_notes,
            "score": self._score,
            "bpm": self._bpm,
            "hand": self._hand,
            "mode": self._mode,
            "auto_speed": self._auto_speed,
            "auto_speed_streak": self._auto_speed_streak,
            "loop_start": self._loop_start,
            "loop_end": self._loop_end,
        }
