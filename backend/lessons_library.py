"""Built-in lesson definitions."""
from typing import List, Dict

# ── Scale helpers ─────────────────────────────────────────────────────────────

MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11, 12]
NATURAL_MINOR_INTERVALS = [0, 2, 3, 5, 7, 8, 10, 12]


def _scale_notes(root: int, intervals: List[int], hand: str = "right") -> List[dict]:
    """One octave up then back down (excluding repeated top note)."""
    up = [root + i for i in intervals]
    down = list(reversed(up[:-1]))
    return [
        {"note": n, "beat": float(i), "duration": 1.0, "hand": hand}
        for i, n in enumerate(up + down)
    ]


def _make_scale(lesson_id, title, root, intervals, hand, bpm=60, difficulty=1, desc=""):
    return {
        "id": lesson_id,
        "title": title,
        "category": "scales",
        "difficulty": difficulty,
        "description": desc or title,
        "default_bpm": bpm,
        "hand": hand,
        "notes": _scale_notes(root, intervals, hand),
    }


# ── Exercise helpers ──────────────────────────────────────────────────────────

def _five_finger(root: int, hand: str = "right") -> List[dict]:
    """Five notes up then down: 1-2-3-4-5-4-3-2-1."""
    notes = [root, root+2, root+4, root+5, root+7, root+5, root+4, root+2, root]
    return [{"note": n, "beat": float(i), "duration": 1.0, "hand": hand} for i, n in enumerate(notes)]


def _make_hanon1() -> List[dict]:
    """Hanon-style exercise #1: ascending broken pattern across 5 positions."""
    # Each group: C E F G A G F E (then up by step)
    notes = []
    beat = 0.0
    for pos in range(5):
        root = 48 + pos * 2  # C3=48, D3=50, E3=52, F3=53, G3=55 (step by major 2nd-ish)
        pattern = [root, root+4, root+5, root+7, root+9, root+7, root+5, root+4]
        for n in pattern:
            notes.append({"note": n, "beat": beat, "duration": 0.5, "hand": "right"})
            beat += 0.5
    # Back down
    for pos in range(4, -1, -1):
        root = 48 + pos * 2
        pattern = [root+9, root+7, root+5, root+4, root+2, root+4, root+5, root+7]
        for n in pattern:
            notes.append({"note": n, "beat": beat, "duration": 0.5, "hand": "right"})
            beat += 0.5
    return notes


# ── Song definitions ──────────────────────────────────────────────────────────

def _note(n, b, d=1.0, h="right", v=80):
    return {"note": n, "beat": b, "duration": d, "hand": h, "velocity": v}


MARY_NOTES = [
    _note(64, 0), _note(62, 1), _note(60, 2), _note(62, 3),
    _note(64, 4), _note(64, 5), _note(64, 6, 2),
    _note(62, 8), _note(62, 9), _note(62, 10, 2),
    _note(64, 12), _note(67, 13), _note(67, 14, 2),
    _note(64, 16), _note(62, 17), _note(60, 18), _note(62, 19),
    _note(64, 20), _note(64, 21), _note(64, 22), _note(64, 23),
    _note(62, 24), _note(62, 25), _note(64, 26), _note(62, 27),
    _note(60, 28, 4),
]

ODE_TO_JOY_RH = [
    _note(64, 0), _note(64, 1), _note(65, 2), _note(67, 3),
    _note(67, 4), _note(65, 5), _note(64, 6), _note(62, 7),
    _note(60, 8), _note(60, 9), _note(62, 10), _note(64, 11),
    _note(64, 12, 1.5), _note(62, 13.5, 0.5), _note(62, 14, 2),
    _note(64, 16), _note(64, 17), _note(65, 18), _note(67, 19),
    _note(67, 20), _note(65, 21), _note(64, 22), _note(62, 23),
    _note(60, 24), _note(60, 25), _note(62, 26), _note(64, 27),
    _note(62, 28, 1.5), _note(60, 29.5, 0.5), _note(60, 30, 2),
]

ODE_TO_JOY_LH = [
    _note(48, 0, 2, "left"), _note(52, 0, 2, "left"), _note(55, 0, 2, "left"),
    _note(47, 2, 2, "left"), _note(50, 2, 2, "left"), _note(55, 2, 2, "left"),
    _note(48, 4, 2, "left"), _note(52, 4, 2, "left"), _note(55, 4, 2, "left"),
    _note(47, 6, 2, "left"), _note(50, 6, 2, "left"), _note(55, 6, 2, "left"),
    _note(48, 8, 2, "left"), _note(52, 8, 2, "left"), _note(55, 8, 2, "left"),
    _note(47, 10, 2, "left"), _note(50, 10, 2, "left"), _note(55, 10, 2, "left"),
    _note(48, 12, 4, "left"), _note(52, 12, 4, "left"), _note(55, 12, 4, "left"),
    _note(48, 16, 2, "left"), _note(52, 16, 2, "left"), _note(55, 16, 2, "left"),
    _note(47, 18, 2, "left"), _note(50, 18, 2, "left"), _note(55, 18, 2, "left"),
    _note(48, 20, 2, "left"), _note(52, 20, 2, "left"), _note(55, 20, 2, "left"),
    _note(47, 22, 2, "left"), _note(50, 22, 2, "left"), _note(55, 22, 2, "left"),
    _note(48, 24, 2, "left"), _note(52, 24, 2, "left"), _note(55, 24, 2, "left"),
    _note(47, 26, 2, "left"), _note(50, 26, 2, "left"), _note(55, 26, 2, "left"),
    _note(48, 28, 4, "left"), _note(52, 28, 4, "left"), _note(55, 28, 4, "left"),
]

TWINKLE_NOTES = [
    _note(60, 0), _note(60, 1), _note(67, 2), _note(67, 3),
    _note(69, 4), _note(69, 5), _note(67, 6, 2),
    _note(65, 8), _note(65, 9), _note(64, 10), _note(64, 11),
    _note(62, 12), _note(62, 13), _note(60, 14, 2),
    _note(67, 16), _note(67, 17), _note(65, 18), _note(65, 19),
    _note(64, 20), _note(64, 21), _note(62, 22, 2),
    _note(67, 24), _note(67, 25), _note(65, 26), _note(65, 27),
    _note(64, 28), _note(64, 29), _note(62, 30, 2),
    _note(60, 32), _note(60, 33), _note(67, 34), _note(67, 35),
    _note(69, 36), _note(69, 37), _note(67, 38, 2),
    _note(65, 40), _note(65, 41), _note(64, 42), _note(64, 43),
    _note(62, 44), _note(62, 45), _note(60, 46, 2),
]

HAPPY_BIRTHDAY_NOTES = [
    _note(55, 0, 0.75), _note(55, 0.75, 0.25),
    _note(57, 1, 1), _note(55, 2, 1), _note(60, 3, 1), _note(59, 4, 2),
    _note(55, 6, 0.75), _note(55, 6.75, 0.25),
    _note(57, 7, 1), _note(55, 8, 1), _note(62, 9, 1), _note(60, 10, 2),
    _note(55, 12, 0.75), _note(55, 12.75, 0.25),
    _note(67, 13, 1), _note(64, 14, 1), _note(60, 15, 1), _note(59, 16, 1), _note(57, 17, 2),
    _note(65, 19, 0.75), _note(65, 19.75, 0.25),
    _note(64, 20, 1), _note(60, 21, 1), _note(62, 22, 1), _note(60, 23, 2),
]

FUR_ELISE_RH = [
    _note(76, 0, 0.5), _note(75, 0.5, 0.5),
    _note(76, 1, 0.5), _note(75, 1.5, 0.5),
    _note(76, 2, 0.5), _note(71, 2.5, 0.5),
    _note(74, 3, 0.5), _note(72, 3.5, 0.5),
    _note(69, 4, 1.5),
    _note(60, 6, 0.5), _note(64, 6.5, 0.5),
    _note(69, 7, 1.5),
    _note(60, 9, 0.5), _note(64, 9.5, 0.5),
    _note(68, 10, 1.5),
    _note(64, 12, 0.5), _note(66, 12.5, 0.5),
    _note(69, 13, 1.5),
    _note(69, 15, 0.5), _note(71, 15.5, 0.5),
    _note(72, 16, 1.5),
    _note(76, 18, 0.5), _note(75, 18.5, 0.5),
    _note(76, 19, 0.5), _note(75, 19.5, 0.5),
    _note(76, 20, 0.5), _note(71, 20.5, 0.5),
    _note(74, 21, 0.5), _note(72, 21.5, 0.5),
    _note(69, 22, 1.5),
]

# ── Chord progressions ────────────────────────────────────────────────────────

def _chord(notes, beat, duration=2.0, hand="right"):
    return [{"note": n, "beat": beat, "duration": duration, "hand": hand} for n in notes]


def _make_basic_triads():
    """C, Am, F, G7 basic chord shapes."""
    notes = []
    notes += _chord([60, 64, 67], 0)       # C major
    notes += _chord([57, 60, 64], 2)       # A minor
    notes += _chord([65, 69, 72], 4)       # F major
    notes += _chord([55, 59, 62, 65], 6)   # G7
    notes += _chord([60, 64, 67], 8, 4)    # C major (resolve)
    return notes


def _make_i_iv_v_i():
    """I-IV-V-I chord progression in C major."""
    notes = []
    notes += _chord([60, 64, 67], 0, 2)    # I  C
    notes += _chord([65, 69, 72], 2, 2)    # IV F
    notes += _chord([67, 71, 74], 4, 2)    # V  G
    notes += _chord([60, 64, 67], 6, 4)    # I  C (resolve)
    return notes


def _make_am_progression():
    """Am - F - C - G (pop progression)."""
    notes = []
    notes += _chord([57, 60, 64], 0, 2)    # Am
    notes += _chord([65, 69, 72], 2, 2)    # F
    notes += _chord([60, 64, 67], 4, 2)    # C
    notes += _chord([55, 59, 62], 6, 2)    # G
    notes += _chord([57, 60, 64], 8, 4)    # Am (repeat/resolve)
    return notes


# ── The full lesson library ───────────────────────────────────────────────────

LESSONS: List[dict] = [
    # --- SCALES ---
    _make_scale(
        "scales/c_major_rh", "C Major Scale — Right Hand",
        60, MAJOR_INTERVALS, "right", bpm=60,
        desc="The foundation of all scales. One octave up and down.",
    ),
    _make_scale(
        "scales/c_major_lh", "C Major Scale — Left Hand",
        48, MAJOR_INTERVALS, "left", bpm=60,
        desc="C major scale starting from C3 with your left hand.",
    ),
    {
        "id": "scales/c_major_both",
        "title": "C Major Scale — Both Hands",
        "category": "scales",
        "difficulty": 2,
        "description": "Both hands play C major in parallel motion, one octave apart.",
        "default_bpm": 50,
        "hand": "both",
        "tracks": {
            "right": _scale_notes(60, MAJOR_INTERVALS, "right"),
            "left":  _scale_notes(48, MAJOR_INTERVALS, "left"),
        },
    },
    _make_scale(
        "scales/g_major_rh", "G Major Scale — Right Hand",
        55, MAJOR_INTERVALS, "right", bpm=60, difficulty=1,
        desc="G major scale (one sharp: F#). Starting G3.",
    ),
    _make_scale(
        "scales/f_major_rh", "F Major Scale — Right Hand",
        65, MAJOR_INTERVALS, "right", bpm=60, difficulty=1,
        desc="F major scale (one flat: Bb). Starting F4.",
    ),
    _make_scale(
        "scales/d_major_rh", "D Major Scale — Right Hand",
        62, MAJOR_INTERVALS, "right", bpm=60, difficulty=2,
        desc="D major scale (two sharps: F#, C#). Starting D4.",
    ),
    _make_scale(
        "scales/a_major_rh", "A Major Scale — Right Hand",
        57, MAJOR_INTERVALS, "right", bpm=60, difficulty=2,
        desc="A major scale (three sharps). Starting A3.",
    ),
    _make_scale(
        "scales/e_major_rh", "E Major Scale — Right Hand",
        64, MAJOR_INTERVALS, "right", bpm=60, difficulty=2,
        desc="E major scale (four sharps). Starting E4.",
    ),
    _make_scale(
        "scales/a_minor_rh", "A Natural Minor Scale — Right Hand",
        57, NATURAL_MINOR_INTERVALS, "right", bpm=60, difficulty=1,
        desc="A natural minor: the relative minor of C major. No sharps or flats.",
    ),

    # --- EXERCISES ---
    {
        "id": "exercises/five_finger_c",
        "title": "Five-Finger Exercise in C",
        "category": "exercises",
        "difficulty": 1,
        "description": "1-2-3-4-5 and back down. Basic finger independence.",
        "default_bpm": 60,
        "hand": "right",
        "notes": _five_finger(60, "right"),
    },
    {
        "id": "exercises/hanon_1",
        "title": "Hanon Exercise No. 1",
        "category": "exercises",
        "difficulty": 2,
        "description": "Classic Hanon broken-chord ascending pattern across five positions.",
        "default_bpm": 60,
        "hand": "right",
        "notes": _make_hanon1(),
    },

    # --- CHORDS ---
    {
        "id": "chords/basic_triads",
        "title": "Basic Triads: C Am F G7",
        "category": "chords",
        "difficulty": 1,
        "description": "Practice four essential chord shapes. Press all three keys together.",
        "default_bpm": 50,
        "hand": "right",
        "notes": _make_basic_triads(),
    },
    {
        "id": "chords/i_iv_v_i",
        "title": "I–IV–V–I Progression in C",
        "category": "chords",
        "difficulty": 2,
        "description": "The most common chord progression in Western music: C F G C.",
        "default_bpm": 50,
        "hand": "right",
        "notes": _make_i_iv_v_i(),
    },
    {
        "id": "chords/am_progression",
        "title": "Am–F–C–G Progression",
        "category": "chords",
        "difficulty": 2,
        "description": "The 'pop' progression used in countless songs.",
        "default_bpm": 50,
        "hand": "right",
        "notes": _make_am_progression(),
    },

    # --- SONGS ---
    {
        "id": "songs/mary_had_a_little_lamb",
        "title": "Mary Had a Little Lamb",
        "category": "songs",
        "difficulty": 1,
        "description": "Classic nursery rhyme. Great first song — uses only E D C G.",
        "default_bpm": 80,
        "hand": "right",
        "notes": MARY_NOTES,
    },
    {
        "id": "songs/twinkle_twinkle",
        "title": "Twinkle Twinkle Little Star",
        "category": "songs",
        "difficulty": 1,
        "description": "Uses the full C major 5-note range. One of the most famous melodies.",
        "default_bpm": 80,
        "hand": "right",
        "notes": TWINKLE_NOTES,
    },
    {
        "id": "songs/happy_birthday",
        "title": "Happy Birthday",
        "category": "songs",
        "difficulty": 2,
        "description": "3/4 feel with a pickup note. Good for practising rhythm.",
        "default_bpm": 70,
        "hand": "right",
        "notes": HAPPY_BIRTHDAY_NOTES,
    },
    {
        "id": "songs/ode_to_joy_rh",
        "title": "Ode to Joy — Right Hand",
        "category": "songs",
        "difficulty": 2,
        "description": "Beethoven's iconic melody. Right hand only.",
        "default_bpm": 80,
        "hand": "right",
        "notes": ODE_TO_JOY_RH,
    },
    {
        "id": "songs/ode_to_joy_both",
        "title": "Ode to Joy — Both Hands",
        "category": "songs",
        "difficulty": 3,
        "description": "Beethoven's melody with left hand chord accompaniment.",
        "default_bpm": 60,
        "hand": "both",
        "tracks": {
            "right": ODE_TO_JOY_RH,
            "left":  ODE_TO_JOY_LH,
        },
    },
    {
        "id": "songs/fur_elise",
        "title": "Für Elise — Opening Theme",
        "category": "songs",
        "difficulty": 3,
        "description": "Beethoven's famous opening phrase. Right hand only, simplified.",
        "default_bpm": 60,
        "hand": "right",
        "notes": FUR_ELISE_RH,
    },
]

_LESSON_MAP: Dict[str, dict] = {l["id"]: l for l in LESSONS}


def get_all_lessons() -> List[dict]:
    return LESSONS


def get_lesson_by_id(lesson_id: str) -> Optional[dict]:
    return _LESSON_MAP.get(lesson_id)


def get_lessons_summary() -> List[dict]:
    """Lightweight list for the sidebar (no note data)."""
    return [
        {
            "id": l["id"],
            "title": l["title"],
            "category": l["category"],
            "difficulty": l["difficulty"],
            "description": l["description"],
            "hand": l.get("hand", "right"),
        }
        for l in LESSONS
    ]
