"""Built-in lesson definitions."""
from typing import List, Dict, Optional

# ── Scale helpers ─────────────────────────────────────────────────────────────

MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11, 12]
NATURAL_MINOR_INTERVALS = [0, 2, 3, 5, 7, 8, 10, 12]
CHROMATIC_INTERVALS = list(range(13))  # 0..12

# Standard RH fingering for major scale (one octave up + down):
# Up:   1 2 3 1 2 3 4 5
# Down: 5 4 3 2 1 3 2 1
_RH_MAJOR_FINGERING = [1, 2, 3, 1, 2, 3, 4, 5, 4, 3, 2, 1, 3, 2, 1]

# Standard LH fingering for major scale (one octave up + down, starting C3):
# Up:   5 4 3 2 1 3 2 1
# Down: 1 2 3 1 2 3 4 5
_LH_MAJOR_FINGERING = [5, 4, 3, 2, 1, 3, 2, 1, 2, 3, 1, 2, 3, 4, 5]

# RH five-finger: 1 2 3 4 5 4 3 2 1
_RH_FIVE_FINGER = [1, 2, 3, 4, 5, 4, 3, 2, 1]
_LH_FIVE_FINGER = [5, 4, 3, 2, 1, 2, 3, 4, 5]


def _scale_notes(root: int, intervals: List[int], hand: str = "right",
                 fingering: Optional[List[int]] = None) -> List[dict]:
    """One octave up then back down (excluding repeated top note)."""
    up = [root + i for i in intervals]
    down = list(reversed(up[:-1]))
    all_notes = up + down
    result = []
    for i, n in enumerate(all_notes):
        note: dict = {"note": n, "beat": float(i), "duration": 1.0, "hand": hand}
        if fingering and i < len(fingering):
            note["finger"] = fingering[i]
        result.append(note)
    return result


def _make_scale(lesson_id, title, root, intervals, hand, bpm=60, difficulty=1, desc="",
                fingering=None):
    return {
        "id": lesson_id,
        "title": title,
        "category": "scales",
        "difficulty": difficulty,
        "description": desc or title,
        "default_bpm": bpm,
        "hand": hand,
        "notes": _scale_notes(root, intervals, hand, fingering),
    }


# ── Exercise helpers ──────────────────────────────────────────────────────────

def _five_finger(root: int, hand: str = "right", fingering: Optional[List[int]] = None) -> List[dict]:
    """Five notes up then down: 1-2-3-4-5-4-3-2-1."""
    notes_seq = [root, root+2, root+4, root+5, root+7, root+5, root+4, root+2, root]
    result = []
    for i, n in enumerate(notes_seq):
        note: dict = {"note": n, "beat": float(i), "duration": 1.0, "hand": hand}
        if fingering and i < len(fingering):
            note["finger"] = fingering[i]
        result.append(note)
    return result


def _make_hanon1() -> List[dict]:
    """Hanon-style exercise #1: ascending broken pattern across 5 positions."""
    notes = []
    beat = 0.0
    for pos in range(5):
        root = 48 + pos * 2
        pattern = [root, root+4, root+5, root+7, root+9, root+7, root+5, root+4]
        for n in pattern:
            notes.append({"note": n, "beat": beat, "duration": 0.5, "hand": "right"})
            beat += 0.5
    for pos in range(4, -1, -1):
        root = 48 + pos * 2
        pattern = [root+9, root+7, root+5, root+4, root+2, root+4, root+5, root+7]
        for n in pattern:
            notes.append({"note": n, "beat": beat, "duration": 0.5, "hand": "right"})
            beat += 0.5
    return notes


def _chromatic_scale(root: int = 60, hand: str = "right") -> List[dict]:
    """Chromatic scale: all 12 semitones up then back down."""
    # RH chromatic fingering: 1 3 1 3 1 1 3 1 3 1 3 1 / 1 3 1 3 1 3 1 1 3 1 3 1
    rh_up   = [1, 3, 1, 3, 1, 1, 3, 1, 3, 1, 3, 1, 1]
    rh_down = list(reversed(rh_up[:-1]))
    fingering = (rh_up + rh_down) if hand == "right" else None
    up = list(range(root, root + 13))
    down = list(reversed(up[:-1]))
    all_notes = up + down
    result = []
    for i, n in enumerate(all_notes):
        note: dict = {"note": n, "beat": float(i) * 0.5, "duration": 0.5, "hand": hand}
        if fingering and i < len(fingering):
            note["finger"] = fingering[i]
        result.append(note)
    return result


def _alberti_bass() -> List[dict]:
    """Classic Alberti bass in C, then F, then G7, then C (8 bars, LH)."""
    notes = []
    beat = 0.0
    # Each bar: 4 beats of root-fifth-third-fifth (all quarter notes)
    progressions = [
        (48, 52, 55),  # C3-E3-G3  (C major, 2 bars)
        (48, 52, 55),
        (53, 57, 60),  # F3-A3-C4  (F major, 2 bars)
        (53, 57, 60),
        (43, 47, 50),  # G2-B2-D3  (G major, 2 bars)
        (43, 47, 50),
        (48, 52, 55),  # C3-E3-G3  (C major, 2 bars)
        (48, 52, 55),
    ]
    for root, third, fifth in progressions:
        for _ in range(4):  # 4 beats per bar
            for n in [root, fifth, third, fifth]:
                notes.append({"note": n, "beat": beat, "duration": 0.25, "hand": "left"})
                beat += 0.25
    return notes


def _interval_exercise(roots: List[int], semitones: int, hand: str = "right") -> List[dict]:
    """Play each root then the note {semitones} above it (2 notes per pair)."""
    notes = []
    beat = 0.0
    for root in roots:
        notes.append({"note": root, "beat": beat, "duration": 1.0, "hand": hand})
        beat += 1.0
        notes.append({"note": root + semitones, "beat": beat, "duration": 1.0, "hand": hand})
        beat += 1.0
    return notes


# ── Song note helper ──────────────────────────────────────────────────────────

def _note(n, b, d=1.0, h="right", v=80):
    return {"note": n, "beat": b, "duration": d, "hand": h, "velocity": v}


# ── Song / piece definitions ──────────────────────────────────────────────────

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

# Jingle Bells chorus (well-known melody, RH)
JINGLE_BELLS_NOTES = [
    # "Jingle bells, jingle bells, jingle all the way"
    _note(64, 0), _note(64, 1), _note(64, 2, 2),      # E E E(half)
    _note(64, 4), _note(64, 5), _note(64, 6, 2),      # E E E(half)
    _note(64, 8), _note(67, 9), _note(60, 10), _note(62, 11),  # E G C D
    _note(64, 12, 4),                                  # E (whole)
    # "Oh what fun it is to ride..."
    _note(65, 16), _note(65, 17), _note(65, 18), _note(65, 19),  # F F F F
    _note(65, 20), _note(64, 21), _note(64, 22), _note(64, 23),  # F E E E
    _note(64, 24), _note(62, 25), _note(62, 26), _note(64, 27),  # E D D E
    _note(62, 28, 2), _note(67, 30, 2),                           # D(half) G(half)
    # "Jingle bells, jingle bells, jingle all the way"
    _note(64, 32), _note(64, 33), _note(64, 34, 2),
    _note(64, 36), _note(64, 37), _note(64, 38, 2),
    _note(64, 40), _note(67, 41), _note(60, 42), _note(62, 43),
    _note(64, 44, 4),
    # "Oh what fun it is to ride in a one-horse open sleigh!"
    _note(65, 48), _note(65, 49), _note(65, 50), _note(65, 51),
    _note(65, 52), _note(64, 53), _note(64, 54), _note(64, 55),
    _note(67, 56), _note(67, 57), _note(65, 58), _note(62, 59),
    _note(60, 60, 4),
]


def _bach_prelude_c() -> List[dict]:
    """Bach Prelude in C (BWV 846) — simplified first 8 bars, broken-chord arpeggios (RH)."""
    # Each bar: 4 pairs of notes (8 eighth notes) ascending arpeggio, repeated
    chords = [
        [60, 64, 67, 72],  # C major  (C4 E4 G4 C5)
        [60, 62, 69, 74],  # Dm7/C   (C4 D4 A4 D5)
        [59, 62, 67, 74],  # G7/B    (B3 D4 G4 D5)
        [57, 60, 64, 69],  # Am      (A3 C4 E4 A4)
        [57, 60, 65, 69],  # F/A     (A3 C4 F4 A4)
        [55, 59, 62, 67],  # G/B     (G3 B3 D4 G4)
        [60, 64, 67, 72],  # C major (repeat)
        [48, 55, 62, 67],  # G7 low  (C3 G3 D4 G4)
    ]
    notes = []
    beat = 0.0
    for chord in chords:
        # Play arpeggio up twice per bar (8 eighth notes)
        for rep in range(2):
            for n in chord:
                notes.append(_note(n, beat, 0.5))
                beat += 0.5
    return notes


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


# ── Find-the-Note trainer — 20 fixed notes spanning C3–C6 ────────────────────

_FIND_NOTE_ROOTS = [
    48, 53, 57, 62, 65, 69, 72, 76, 79, 55,
    60, 64, 67, 71, 74, 50, 56, 61, 68, 75,
]


def _find_the_note_lesson() -> List[dict]:
    """20 notes spread across the keyboard — find each one."""
    return [
        {"note": n, "beat": float(i), "duration": 1.0, "hand": "right"}
        for i, n in enumerate(_FIND_NOTE_ROOTS)
    ]


# ── New song note data ────────────────────────────────────────────────────────

# Hot Cross Buns — simplest canonical 3-note melody (E D C), universal first song
HOT_CROSS_BUNS_NOTES = [
    _note(64, 0), _note(62, 1), _note(60, 2, 2),              # E D C(half)
    _note(64, 4), _note(62, 5), _note(60, 6, 2),              # E D C(half)
    _note(60, 8), _note(60, 9), _note(60, 10), _note(60, 11), # C C C C
    _note(62, 12), _note(62, 13), _note(62, 14), _note(62, 15), # D D D D
    _note(64, 16), _note(62, 17), _note(60, 18, 2),            # E D C(half)
]

# Au Clair de la Lune — French folk song, uses only C D E (Suzuki Book 1, piece 10)
AU_CLAIR_DE_LA_LUNE_NOTES = [
    # Phrase 1: "Au clair de la lu-ne"
    _note(60, 0), _note(60, 1), _note(60, 2), _note(62, 3),
    _note(64, 4, 2), _note(62, 6, 2),
    # Phrase 2: "Mon ami Pierrot"
    _note(60, 8), _note(64, 9), _note(62, 10), _note(62, 11),
    _note(60, 12, 4),
    # Phrases 3-4 (repeat)
    _note(60, 16), _note(60, 17), _note(60, 18), _note(62, 19),
    _note(64, 20, 2), _note(62, 22, 2),
    _note(60, 24), _note(64, 25), _note(62, 26), _note(62, 27),
    _note(60, 28, 4),
]

# Frère Jacques — uses C D E F G A (Suzuki Book 1; appears in all major methods)
FRERE_JACQUES_NOTES = [
    # Phrase 1 x2: "Frère Jacques"
    _note(60, 0), _note(62, 1), _note(64, 2), _note(60, 3),
    _note(60, 4), _note(62, 5), _note(64, 6), _note(60, 7),
    # Phrase 2 x2: "Dormez-vous?"
    _note(64, 8), _note(65, 9), _note(67, 10, 2),
    _note(64, 12), _note(65, 13), _note(67, 14, 2),
    # Phrase 3 x2: "Sonnez les matines" (eighth-note run: G A G F E C)
    _note(67, 16, 0.5), _note(69, 16.5, 0.5), _note(67, 17, 0.5), _note(65, 17.5, 0.5), _note(64, 18), _note(60, 19),
    _note(67, 20, 0.5), _note(69, 20.5, 0.5), _note(67, 21, 0.5), _note(65, 21.5, 0.5), _note(64, 22), _note(60, 23),
    # Phrase 4 x2: "Din din don" (C G3 C half)
    _note(60, 24), _note(55, 25), _note(60, 26, 2),
    _note(60, 28), _note(55, 29), _note(60, 30, 2),
]

# Lightly Row — Suzuki Book 1, piece 2; uses G E F D C
LIGHTLY_ROW_NOTES = [
    # Phrase A (bars 1-4)
    _note(67, 0), _note(64, 1), _note(64, 2, 2),               # G4 E4 E4(half)
    _note(65, 4), _note(62, 5), _note(62, 6, 2),               # F4 D4 D4(half)
    _note(60, 8), _note(62, 9), _note(64, 10), _note(65, 11),  # C4 D4 E4 F4
    _note(67, 12), _note(67, 13), _note(67, 14, 2),            # G4 G4 G4(half)
    # Phrase B (bars 5-8)
    _note(64, 16), _note(64, 17), _note(64, 18), _note(64, 19), # E4 x4
    _note(64, 20), _note(65, 21), _note(67, 22, 2),             # E4 F4 G4(half)
    _note(65, 24), _note(65, 25), _note(65, 26), _note(65, 27), # F4 x4
    _note(65, 28), _note(64, 29), _note(64, 30, 2),             # F4 E4 E4(half)
    # Phrase A' (bars 9-12)
    _note(67, 32), _note(67, 33), _note(67, 34), _note(67, 35), # G4 x4
    _note(67, 36), _note(65, 37), _note(65, 38, 2),             # G4 F4 F4(half)
    _note(64, 40), _note(64, 41), _note(64, 42), _note(64, 43), # E4 x4
    _note(64, 44), _note(62, 45), _note(62, 46, 2),             # E4 D4 D4(half)
    # Phrase B' (bars 13-16)
    _note(60, 48), _note(62, 49), _note(64, 50), _note(65, 51), # C4 D4 E4 F4
    _note(67, 52), _note(67, 53), _note(67, 54, 2),             # G4 G4 G4(half)
    _note(60, 56), _note(64, 57), _note(67, 58), _note(67, 59), # C4 E4 G4 G4
    _note(60, 60, 4),                                            # C4(whole)
]

# Go Tell Aunt Rhody — Suzuki Book 1, piece 9; G E C D range
GO_TELL_AUNT_RHODY_NOTES = [
    # "Go tell Aunt Rhody" x3
    _note(67, 0), _note(64, 1), _note(64, 2, 2),               # G4 E4 E4(half)
    _note(67, 4), _note(64, 5), _note(64, 6, 2),               # G4 E4 E4(half)
    _note(67, 8), _note(64, 9), _note(60, 10), _note(62, 11),  # G4 E4 C4 D4
    _note(64, 12, 2), _note(62, 14, 2),                         # E4(half) D4(half)
    # "The one she was saving"
    _note(60, 16), _note(62, 17), _note(64, 18), _note(65, 19), # C4 D4 E4 F4
    _note(67, 20, 4),                                            # G4(whole)
    _note(65, 24), _note(64, 25), _note(62, 26), _note(64, 27), # F4 E4 D4 E4
    _note(60, 28, 4),                                            # C4(whole)
]

# Minuet in G (Petzold, BWV Anh. 114) — Level 3 milestone in every method
# G major (F# = MIDI 66 = F#4, F#5 = 78). 3/4 time: each beat = 1 quarter note.
MINUET_IN_G_NOTES = [
    # Section A (bars 1-8, beats 0-23)
    _note(62, 0), _note(67, 1), _note(69, 2),          # Bar 1:  D4 G4 A4
    _note(71, 3), _note(72, 4), _note(74, 5),           # Bar 2:  B4 C5 D5
    _note(76, 6, 2), _note(74, 8),                      # Bar 3:  E5(half) D5
    _note(71, 9, 3),                                     # Bar 4:  B4(dotted half)
    _note(72, 12), _note(71, 13), _note(69, 14),        # Bar 5:  C5 B4 A4
    _note(71, 15), _note(67, 16), _note(69, 17),        # Bar 6:  B4 G4 A4
    _note(71, 18, 2), _note(69, 20),                    # Bar 7:  B4(half) A4
    _note(67, 21, 3),                                    # Bar 8:  G4(dotted half)
    # Section A repeat (bars 9-16, beats 24-47)
    _note(62, 24), _note(67, 25), _note(69, 26),
    _note(71, 27), _note(72, 28), _note(74, 29),
    _note(76, 30, 2), _note(74, 32),
    _note(71, 33, 3),
    _note(72, 36), _note(71, 37), _note(69, 38),
    _note(71, 39), _note(67, 40), _note(69, 41),
    _note(71, 42, 2), _note(69, 44),
    _note(67, 45, 3),
    # Section B (bars 17-24, beats 48-71)
    _note(79, 48), _note(78, 49), _note(76, 50),        # Bar 17: G5 F#5 E5
    _note(74, 51), _note(79, 52), _note(78, 53),        # Bar 18: D5 G5 F#5
    _note(76, 54, 2), _note(74, 56),                    # Bar 19: E5(half) D5
    _note(72, 57, 3),                                    # Bar 20: C5(dotted half)
    _note(71, 60), _note(74, 61), _note(72, 62),        # Bar 21: B4 D5 C5
    _note(71, 63), _note(69, 64), _note(67, 65),        # Bar 22: B4 A4 G4
    _note(66, 66, 2), _note(67, 68),                    # Bar 23: F#4(half) G4
    _note(62, 69, 3),                                    # Bar 24: D4(dotted half)
    # Section B' (bars 25-32, beats 72-95)
    _note(67, 72), _note(69, 73), _note(71, 74),        # Bar 25: G4 A4 B4
    _note(72, 75), _note(74, 76), _note(76, 77),        # Bar 26: C5 D5 E5
    _note(78, 78), _note(74, 79), _note(76, 80),        # Bar 27: F#5 D5 E5
    _note(74, 81, 3),                                    # Bar 28: D5(dotted half)
    _note(79, 84), _note(78, 85), _note(76, 86),        # Bar 29: G5 F#5 E5
    _note(78, 87), _note(76, 88), _note(74, 89),        # Bar 30: F#5 E5 D5
    _note(67, 90, 2), _note(62, 92),                    # Bar 31: G4(half) D4
    _note(67, 93, 3),                                    # Bar 32: G4(dotted half)
]


# ── New exercise helpers ───────────────────────────────────────────────────────

def _contrary_motion_c_major() -> List[dict]:
    """Both hands start on C4/C4 and move outward (contrary motion), then return."""
    rh_up   = [60, 62, 64, 65, 67, 69, 71, 72]   # C4..C5
    lh_down = [60, 59, 57, 55, 53, 52, 50, 48]   # C4..C3
    notes = []
    beat = 0.0
    for r, l in zip(rh_up, lh_down):
        notes.append({"note": r, "beat": beat, "duration": 1.0, "hand": "right"})
        notes.append({"note": l, "beat": beat, "duration": 1.0, "hand": "left"})
        beat += 1.0
    for r, l in zip(reversed(rh_up[:-1]), reversed(lh_down[:-1])):
        notes.append({"note": r, "beat": beat, "duration": 1.0, "hand": "right"})
        notes.append({"note": l, "beat": beat, "duration": 1.0, "hand": "left"})
        beat += 1.0
    return notes


def _five_finger_broken_chord() -> List[dict]:
    """Czerny-style broken-chord 5-finger exercise: root-3rd-5th-3rd pattern through C positions."""
    notes = []
    beat = 0.0
    positions = [
        (60, 64, 67),  # C major
        (62, 65, 69),  # Dm
        (64, 67, 71),  # Em
        (65, 69, 72),  # F major
        (67, 71, 74),  # G major
        (65, 69, 72),  # F (descend)
        (62, 65, 69),  # Dm (descend)
        (60, 64, 67),  # C major (final)
    ]
    for root, third, fifth in positions:
        for n in [root, third, fifth, third, root, third, fifth, third]:
            notes.append({"note": n, "beat": beat, "duration": 0.5, "hand": "right"})
            beat += 0.5
    return notes


# ── The full lesson library ───────────────────────────────────────────────────

LESSONS: List[dict] = [
    # ── SCALES ──────────────────────────────────────────────────────────────
    _make_scale(
        "scales/c_major_rh", "C Major Scale — Right Hand",
        60, MAJOR_INTERVALS, "right", bpm=60,
        desc="The foundation of all scales. One octave up and down.",
        fingering=_RH_MAJOR_FINGERING,
    ),
    _make_scale(
        "scales/c_major_lh", "C Major Scale — Left Hand",
        48, MAJOR_INTERVALS, "left", bpm=60,
        desc="C major scale starting from C3 with your left hand.",
        fingering=_LH_MAJOR_FINGERING,
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
            "right": _scale_notes(60, MAJOR_INTERVALS, "right", _RH_MAJOR_FINGERING),
            "left":  _scale_notes(48, MAJOR_INTERVALS, "left",  _LH_MAJOR_FINGERING),
        },
    },
    _make_scale(
        "scales/g_major_rh", "G Major Scale — Right Hand",
        55, MAJOR_INTERVALS, "right", bpm=60, difficulty=1,
        desc="G major scale (one sharp: F#). Starting G3.",
        fingering=_RH_MAJOR_FINGERING,
    ),
    _make_scale(
        "scales/f_major_rh", "F Major Scale — Right Hand",
        65, MAJOR_INTERVALS, "right", bpm=60, difficulty=2,
        desc="F major scale (one flat: Bb). Starting F4. Thumb crosses on Bb — slightly different from C/G/D/A/E.",
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
    {
        "id": "scales/chromatic_rh",
        "title": "Chromatic Scale — Right Hand",
        "category": "scales",
        "difficulty": 2,
        "description": "All 12 semitones: C4 up to C5 and back. Builds awareness of every key.",
        "default_bpm": 60,
        "hand": "right",
        "notes": _chromatic_scale(60, "right"),
    },

    # ── EXERCISES ────────────────────────────────────────────────────────────
    {
        "id": "exercises/five_finger_c",
        "title": "Five-Finger Exercise in C",
        "category": "exercises",
        "difficulty": 1,
        "description": "1-2-3-4-5 and back down. Basic finger independence.",
        "default_bpm": 60,
        "hand": "right",
        "notes": _five_finger(60, "right", _RH_FIVE_FINGER),
    },
    {
        "id": "exercises/five_finger_lh",
        "title": "Five-Finger Exercise in C — Left Hand",
        "category": "exercises",
        "difficulty": 1,
        "description": "LH five-finger exercise: 5-4-3-2-1 and back up.",
        "default_bpm": 60,
        "hand": "left",
        "notes": _five_finger(48, "left", _LH_FIVE_FINGER),
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
    {
        "id": "exercises/alberti_bass",
        "title": "Alberti Bass in C",
        "category": "exercises",
        "difficulty": 2,
        "description": "Classic LH accompaniment pattern (root-fifth-third-fifth). C–F–G–C progression.",
        "default_bpm": 60,
        "hand": "left",
        "notes": _alberti_bass(),
    },
    {
        "id": "exercises/intervals_thirds",
        "title": "Interval Exercise: Major & Minor 3rds",
        "category": "exercises",
        "difficulty": 2,
        "description": "Play each root then the third above. Trains the most common interval in chords.",
        "default_bpm": 60,
        "hand": "right",
        "notes": _interval_exercise([60, 62, 64, 65, 67, 69, 71, 72], 4),  # major thirds up C scale
    },
    {
        "id": "exercises/intervals_fifths",
        "title": "Interval Exercise: Perfect 5ths",
        "category": "exercises",
        "difficulty": 2,
        "description": "Play each root then the fifth above. The most stable interval in Western music.",
        "default_bpm": 60,
        "hand": "right",
        "notes": _interval_exercise([60, 62, 64, 65, 67, 69, 71, 72], 7),  # perfect fifths
    },
    {
        "id": "exercises/intervals_octaves",
        "title": "Interval Exercise: Octaves",
        "category": "exercises",
        "difficulty": 3,
        "description": "Play each note then the octave above. Stretches the hand and trains position jumps.",
        "default_bpm": 50,
        "hand": "right",
        "notes": _interval_exercise([60, 62, 64, 65, 67], 12),
    },
    {
        "id": "exercises/five_finger_g",
        "title": "Five-Finger Exercise in G",
        "category": "exercises",
        "difficulty": 1,
        "description": "G position: G A B C D and back. Natural next step after the C five-finger exercise.",
        "default_bpm": 60,
        "hand": "right",
        "notes": _five_finger(67, "right", _RH_FIVE_FINGER),
    },
    {
        "id": "exercises/five_finger_f",
        "title": "Five-Finger Exercise in F",
        "category": "exercises",
        "difficulty": 2,
        "description": "F position: F G A Bb C and back. Introduces Bb — the one flat key's distinctive note.",
        "default_bpm": 60,
        "hand": "right",
        "notes": _five_finger(65, "right", _RH_FIVE_FINGER),
    },
    {
        "id": "exercises/contrary_motion_c",
        "title": "Contrary Motion Scale — C Major",
        "category": "exercises",
        "difficulty": 2,
        "description": "Both hands start on C4 and move outward simultaneously. Consensus first two-hand scale exercise.",
        "default_bpm": 60,
        "hand": "both",
        "notes": _contrary_motion_c_major(),
    },
    {
        "id": "exercises/broken_chord_c",
        "title": "Broken-Chord Exercise in C (Czerny-Style)",
        "category": "exercises",
        "difficulty": 2,
        "description": "Root-3rd-5th-3rd pattern through C major positions. Builds hand independence and arpeggiation.",
        "default_bpm": 60,
        "hand": "right",
        "notes": _five_finger_broken_chord(),
    },

    # ── CHORDS ───────────────────────────────────────────────────────────────
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

    # ── SONGS ────────────────────────────────────────────────────────────────
    {
        "id": "songs/hot_cross_buns",
        "title": "Hot Cross Buns",
        "category": "songs",
        "difficulty": 1,
        "description": "The simplest first melody — only 3 notes: E D C. Used in all major beginner methods.",
        "default_bpm": 80,
        "hand": "right",
        "notes": HOT_CROSS_BUNS_NOTES,
    },
    {
        "id": "songs/au_clair_de_la_lune",
        "title": "Au Clair de la Lune",
        "category": "songs",
        "difficulty": 1,
        "description": "French folk song using only C D E. Suzuki Book 1, piece 10.",
        "default_bpm": 80,
        "hand": "right",
        "notes": AU_CLAIR_DE_LA_LUNE_NOTES,
    },
    {
        "id": "songs/frere_jacques",
        "title": "Frère Jacques",
        "category": "songs",
        "difficulty": 1,
        "description": "Rounds canon using C D E F G A. Classic in all beginner methods.",
        "default_bpm": 90,
        "hand": "right",
        "notes": FRERE_JACQUES_NOTES,
    },
    {
        "id": "songs/lightly_row",
        "title": "Lightly Row",
        "category": "songs",
        "difficulty": 1,
        "description": "Suzuki Book 1, piece 2. Uses G E F D C — good for hand position stability.",
        "default_bpm": 90,
        "hand": "right",
        "notes": LIGHTLY_ROW_NOTES,
    },
    {
        "id": "songs/go_tell_aunt_rhody",
        "title": "Go Tell Aunt Rhody",
        "category": "songs",
        "difficulty": 1,
        "description": "Suzuki Book 1, piece 9. Uses G E C D F — broadens range beyond 5-finger.",
        "default_bpm": 80,
        "hand": "right",
        "notes": GO_TELL_AUNT_RHODY_NOTES,
    },
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
        "id": "songs/jingle_bells",
        "title": "Jingle Bells",
        "category": "songs",
        "difficulty": 1,
        "description": "The famous chorus. Uses C D E F G — all white keys.",
        "default_bpm": 100,
        "hand": "right",
        "notes": JINGLE_BELLS_NOTES,
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
    {
        "id": "songs/bach_prelude_c",
        "title": "Bach Prelude in C (Simplified)",
        "category": "songs",
        "difficulty": 3,
        "description": "BWV 846 broken-chord arpeggios. First 8 bars, right hand only. Pure chord exploration.",
        "default_bpm": 60,
        "hand": "right",
        "notes": _bach_prelude_c(),
    },
    {
        "id": "songs/minuet_in_g",
        "title": "Minuet in G (Petzold)",
        "category": "songs",
        "difficulty": 3,
        "description": "BWV Anh. 114 — G major, 3/4. Full 32-bar piece. Level 3 milestone in every major method.",
        "default_bpm": 116,
        "hand": "right",
        "notes": MINUET_IN_G_NOTES,
    },

    # ── TRAINER ──────────────────────────────────────────────────────────────
    {
        "id": "trainer/find_the_note",
        "title": "Find the Note",
        "category": "trainer",
        "difficulty": 1,
        "description": "20 notes spread across the keyboard. Find each highlighted key — trains keyboard geography.",
        "default_bpm": 999,   # no tempo — wait mode only
        "hand": "right",
        "notes": _find_the_note_lesson(),
    },
    {
        "id": "trainer/keyboard_thirds",
        "title": "Keyboard Trainer: Thirds",
        "category": "trainer",
        "difficulty": 2,
        "description": "Play a root then the major third above it. Trains interval recognition across the keyboard.",
        "default_bpm": 60,
        "hand": "right",
        "notes": _interval_exercise([60, 64, 67, 71, 74, 55, 59, 62, 65, 69], 4),
    },
    {
        "id": "trainer/keyboard_fifths",
        "title": "Keyboard Trainer: Perfect 5ths",
        "category": "trainer",
        "difficulty": 2,
        "description": "Play a root then the perfect fifth above. Master the most important interval.",
        "default_bpm": 60,
        "hand": "right",
        "notes": _interval_exercise([60, 62, 64, 65, 67, 69, 71, 55, 57, 59], 7),
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
