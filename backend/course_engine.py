"""Course progression engine.

Manages a sequential curriculum of piano lessons with strict mastery gates:
  - ≥90% accuracy AND BPM ≥ min_bpm (where set) counts as a "pass"
  - 3 consecutive passes → lesson mastered → next lesson unlocked
  - Mastered lessons idle >14 days are flagged for spaced-repetition review
A diagnostic lesson at the start determines where in the curriculum to begin.
"""

import json
import logging
import os
import time
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

MASTERY_ACCURACY    = 90   # minimum accuracy % to count as a pass
MASTERY_CONSECUTIVE = 3    # consecutive passes needed to master a lesson
REVIEW_DAYS         = 14   # days after mastery before a review is suggested

_SCHEMA_VERSION = 2        # increment when progress format changes

# ── Curriculum ────────────────────────────────────────────────────────────────
# min_bpm: if set, the attempt BPM must be ≥ min_bpm for the pass to count.
# Omit for songs/chords where accuracy matters more than tempo.

CURRICULUM: List[Dict] = [
    # ── Diagnóstico ──────────────────────────────────────────────────────────
    {
        "lesson_id": "diagnostic/assessment",
        "hand":      "right",
        "stage":     "Diagnóstico",
        "label":     "Avaliação Inicial",
    },

    # ── Etapa 1: Mão Direita ─────────────────────────────────────────────────
    {
        "lesson_id": "exercises/five_finger_c",
        "hand":      "right",
        "stage":     "Etapa 1: Mão Direita",
        "label":     "Cinco Dedos em Dó",
        "min_bpm":   60,
    },
    {
        "lesson_id": "songs/hot_cross_buns",
        "hand":      "right",
        "stage":     "Etapa 1: Mão Direita",
        "label":     "Hot Cross Buns",
    },
    {
        "lesson_id": "songs/mary_had_a_little_lamb",
        "hand":      "right",
        "stage":     "Etapa 1: Mão Direita",
        "label":     "Mary Had a Little Lamb",
    },
    {
        "lesson_id": "songs/au_clair_de_la_lune",
        "hand":      "right",
        "stage":     "Etapa 1: Mão Direita",
        "label":     "Au Clair de la Lune",
    },
    {
        "lesson_id": "scales/c_major_rh",
        "hand":      "right",
        "stage":     "Etapa 1: Mão Direita",
        "label":     "Escala de Dó Maior (MD)",
        "min_bpm":   60,
    },

    # ── Etapa 2: Mão Esquerda ────────────────────────────────────────────────
    {
        "lesson_id": "exercises/five_finger_lh",
        "hand":      "left",
        "stage":     "Etapa 2: Mão Esquerda",
        "label":     "Cinco Dedos em Dó (ME)",
        "min_bpm":   60,
    },
    {
        "lesson_id": "scales/c_major_lh",
        "hand":      "left",
        "stage":     "Etapa 2: Mão Esquerda",
        "label":     "Escala de Dó Maior (ME)",
        "min_bpm":   60,
    },

    # ── Etapa 3: Coordenação ─────────────────────────────────────────────────
    {
        "lesson_id": "exercises/contrary_motion_c",
        "hand":      "both",
        "stage":     "Etapa 3: Coordenação",
        "label":     "Movimento Contrário em Dó",
        "min_bpm":   50,
    },
    {
        "lesson_id": "scales/c_major_both",
        "hand":      "both",
        "stage":     "Etapa 3: Coordenação",
        "label":     "Escala de Dó (Ambas as Mãos)",
        "min_bpm":   50,
    },
    {
        "lesson_id": "songs/frere_jacques",
        "hand":      "right",
        "stage":     "Etapa 3: Coordenação",
        "label":     "Frère Jacques",
    },
    {
        "lesson_id": "songs/twinkle_twinkle",
        "hand":      "right",
        "stage":     "Etapa 3: Coordenação",
        "label":     "Twinkle Twinkle",
    },
    {
        "lesson_id": "chords/basic_triads",
        "hand":      "right",
        "stage":     "Etapa 3: Coordenação",
        "label":     "Acordes Básicos",
    },

    # ── Etapa 4: Novas Tonalidades ───────────────────────────────────────────
    {
        "lesson_id": "chords/i_iv_v_i",
        "hand":      "right",
        "stage":     "Etapa 4: Novas Tonalidades",
        "label":     "Progressão I-IV-V-I",
    },
    {
        "lesson_id": "scales/g_major_rh",
        "hand":      "right",
        "stage":     "Etapa 4: Novas Tonalidades",
        "label":     "Escala de Sol Maior",
        "min_bpm":   60,
    },
    {
        "lesson_id": "scales/f_major_rh",
        "hand":      "right",
        "stage":     "Etapa 4: Novas Tonalidades",
        "label":     "Escala de Fá Maior",
        "min_bpm":   60,
    },
    {
        "lesson_id": "songs/lightly_row",
        "hand":      "right",
        "stage":     "Etapa 4: Novas Tonalidades",
        "label":     "Lightly Row",
    },
    {
        "lesson_id": "exercises/five_finger_g",
        "hand":      "right",
        "stage":     "Etapa 4: Novas Tonalidades",
        "label":     "Cinco Dedos em Sol",
        "min_bpm":   60,
    },

    # ── Etapa 5: Técnica ─────────────────────────────────────────────────────
    {
        "lesson_id": "exercises/hanon_1",
        "hand":      "right",
        "stage":     "Etapa 5: Técnica",
        "label":     "Hanon No. 1",
        "min_bpm":   80,
    },
    {
        "lesson_id": "exercises/alberti_bass",
        "hand":      "left",
        "stage":     "Etapa 5: Técnica",
        "label":     "Baixo Alberti",
        "min_bpm":   60,
    },
    {
        "lesson_id": "chords/am_progression",
        "hand":      "right",
        "stage":     "Etapa 5: Técnica",
        "label":     "Progressão Am-F-C-G",
    },
    {
        "lesson_id": "songs/happy_birthday",
        "hand":      "right",
        "stage":     "Etapa 5: Técnica",
        "label":     "Happy Birthday",
    },
    {
        "lesson_id": "songs/minuet_in_g",
        "hand":      "right",
        "stage":     "Etapa 5: Técnica",
        "label":     "Minueto em Sol",
    },
    {
        "lesson_id": "songs/go_tell_aunt_rhody",
        "hand":      "right",
        "stage":     "Etapa 5: Técnica",
        "label":     "Go Tell Aunt Rhody",
    },

    # ── Etapa 6: Repertório ──────────────────────────────────────────────────
    {
        "lesson_id": "scales/a_minor_rh",
        "hand":      "right",
        "stage":     "Etapa 6: Repertório",
        "label":     "Escala de Lá Menor",
        "min_bpm":   60,
    },
    {
        "lesson_id": "exercises/broken_chord_c",
        "hand":      "right",
        "stage":     "Etapa 6: Repertório",
        "label":     "Arpejos em Dó",
        "min_bpm":   60,
    },
    {
        "lesson_id": "songs/ode_to_joy_rh",
        "hand":      "right",
        "stage":     "Etapa 6: Repertório",
        "label":     "Ode à Alegria",
    },
    {
        "lesson_id": "songs/jingle_bells",
        "hand":      "right",
        "stage":     "Etapa 6: Repertório",
        "label":     "Jingle Bells",
    },
    {
        "lesson_id": "songs/fur_elise",
        "hand":      "right",
        "stage":     "Etapa 6: Repertório",
        "label":     "Für Elise",
    },

    # ── Etapa 7: Maestria ────────────────────────────────────────────────────
    {
        "lesson_id": "scales/d_major_rh",
        "hand":      "right",
        "stage":     "Etapa 7: Maestria",
        "label":     "Escala de Ré Maior",
        "min_bpm":   80,
    },
    {
        "lesson_id": "scales/a_major_rh",
        "hand":      "right",
        "stage":     "Etapa 7: Maestria",
        "label":     "Escala de Lá Maior",
        "min_bpm":   80,
    },
    {
        "lesson_id": "exercises/intervals_thirds",
        "hand":      "right",
        "stage":     "Etapa 7: Maestria",
        "label":     "Intervalos: Terças",
        "min_bpm":   60,
    },
    {
        "lesson_id": "scales/chromatic_rh",
        "hand":      "right",
        "stage":     "Etapa 7: Maestria",
        "label":     "Escala Cromática",
        "min_bpm":   60,
    },
    {
        "lesson_id": "songs/bach_prelude_c",
        "hand":      "right",
        "stage":     "Etapa 7: Maestria",
        "label":     "Prelúdio de Bach em Dó",
    },
]

# Fast lookup: (lesson_id, hand) → curriculum entry
_CURRICULUM_INDEX: Dict = {
    (s["lesson_id"], s["hand"]): s for s in CURRICULUM
}


class CourseEngine:
    def __init__(self, progress_file: str = "data/course_progress.json"):
        self._progress_file = progress_file
        self._progress = self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if os.path.exists(self._progress_file):
            try:
                with open(self._progress_file) as f:
                    data = json.load(f)
                data = self._migrate(data)
                return data
            except Exception as exc:
                log.warning("Could not load course progress (%s) — starting fresh", exc)
        return self._defaults()

    def _defaults(self) -> dict:
        return {
            "version":           _SCHEMA_VERSION,
            "diagnostic_complete": False,
            "current_index":     0,
            "starting_index":    0,
            # "{lesson_id}:{hand}" → {consecutive, passes, best_accuracy,
            #                         best_bpm, attempts, last_passed_at}
            "mastery": {},
        }

    def _migrate(self, data: dict) -> dict:
        v = data.get("version", 0)
        if v < 1:
            # Version 0→1: add version field
            data["version"] = 1
        if v < 2:
            # Version 1→2: add best_bpm and last_passed_at to mastery entries
            for key, m in data.get("mastery", {}).items():
                m.setdefault("best_bpm", 0.0)
                m.setdefault("last_passed_at", None)
            data["version"] = 2
        return data

    def _save(self):
        folder = os.path.dirname(self._progress_file)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(self._progress_file, "w") as f:
            json.dump(self._progress, f, indent=2)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _key(self, lesson_id: str, hand: str) -> str:
        return f"{lesson_id}:{hand}"

    def _mastery_data(self, lesson_id: str, hand: str) -> dict:
        return dict(self._progress["mastery"].get(self._key(lesson_id, hand), {
            "consecutive":    0,
            "passes":         0,
            "best_accuracy":  0.0,
            "best_bpm":       0.0,
            "attempts":       0,
            "last_passed_at": None,
        }))

    # ── Public queries ────────────────────────────────────────────────────────

    def is_mastered(self, lesson_id: str, hand: str) -> bool:
        return self._mastery_data(lesson_id, hand)["consecutive"] >= MASTERY_CONSECUTIVE

    def is_unlocked(self, index: int) -> bool:
        if index == 0:
            return True
        for i in range(index):
            step = CURRICULUM[i]
            if not self.is_mastered(step["lesson_id"], step["hand"]):
                return False
        return True

    def needs_review(self, lesson_id: str, hand: str) -> bool:
        """True when the lesson is mastered but hasn't been played in REVIEW_DAYS."""
        m = self._mastery_data(lesson_id, hand)
        if m["consecutive"] < MASTERY_CONSECUTIVE:
            return False
        lp = m.get("last_passed_at")
        if lp is None:
            return False
        return (time.time() - lp) > REVIEW_DAYS * 86400

    def get_current_step(self) -> Optional[dict]:
        idx = self._progress["current_index"]
        return CURRICULUM[idx] if idx < len(CURRICULUM) else None

    def get_min_bpm(self, lesson_id: str, hand: str) -> Optional[float]:
        step = _CURRICULUM_INDEX.get((lesson_id, hand))
        return step.get("min_bpm") if step else None

    # ── Recording attempts ────────────────────────────────────────────────────

    def record_attempt(self, lesson_id: str, hand: str,
                       accuracy: float, bpm: float = 0.0) -> dict:
        """Record a completed lesson attempt. Returns a feedback dict."""
        key = self._key(lesson_id, hand)
        m   = self._mastery_data(lesson_id, hand)
        m.setdefault("best_bpm", 0.0)
        m.setdefault("last_passed_at", None)

        m["attempts"] += 1

        # BPM gate: attempt must meet min_bpm if defined
        step    = _CURRICULUM_INDEX.get((lesson_id, hand), {})
        min_bpm = step.get("min_bpm")
        bpm_ok  = (min_bpm is None) or (bpm >= min_bpm)

        accuracy_ok = accuracy >= MASTERY_ACCURACY
        passed      = accuracy_ok and bpm_ok

        if passed:
            m["consecutive"]    += 1
            m["passes"]         += 1
            m["last_passed_at"]  = time.time()
        else:
            m["consecutive"] = 0

        if accuracy > m["best_accuracy"]:
            m["best_accuracy"] = accuracy
        if bpm > m["best_bpm"]:
            m["best_bpm"] = bpm

        self._progress["mastery"][key] = m

        # Diagnostic: auto-complete and choose entry point
        is_diagnostic = lesson_id == "diagnostic/assessment"
        if is_diagnostic and not self._progress["diagnostic_complete"]:
            self._progress["diagnostic_complete"] = True
            m["consecutive"] = MASTERY_CONSECUTIVE
            self._progress["mastery"][key] = m
            start = self._start_index_from_accuracy(accuracy)
            self._progress["starting_index"] = start
            self._progress["current_index"]  = start

        # Advance current_index when the active lesson is freshly mastered
        newly_mastered = m["consecutive"] >= MASTERY_CONSECUTIVE
        cur = self._progress["current_index"]
        if newly_mastered and cur < len(CURRICULUM):
            cur_step = CURRICULUM[cur]
            if cur_step["lesson_id"] == lesson_id and cur_step["hand"] == hand:
                self._progress["current_index"] = min(cur + 1, len(CURRICULUM))

        self._save()
        return {
            "passed":          passed,
            "accuracy_ok":     accuracy_ok,
            "bpm_ok":          bpm_ok,
            "newly_mastered":  newly_mastered,
            "consecutive":     m["consecutive"],
            "needed":          MASTERY_CONSECUTIVE,
            "accuracy":        accuracy,
            "best_accuracy":   m["best_accuracy"],
            "bpm":             bpm,
            "min_bpm":         min_bpm,
            "is_diagnostic":   is_diagnostic,
        }

    def _start_index_from_accuracy(self, acc: float) -> int:
        if acc >= 80:
            return self._first_index_of("Etapa 3: Coordenação")
        if acc >= 60:
            return self._first_index_of("Etapa 2: Mão Esquerda")
        return self._first_index_of("Etapa 1: Mão Direita")

    def _first_index_of(self, stage: str) -> int:
        for i, step in enumerate(CURRICULUM):
            if step["stage"] == stage:
                return i
        return 1

    # ── State export ──────────────────────────────────────────────────────────

    def get_state(self) -> dict:
        now = time.time()
        curriculum_out = []
        for i, step in enumerate(CURRICULUM):
            m       = self._mastery_data(step["lesson_id"], step["hand"])
            mastered = m["consecutive"] >= MASTERY_CONSECUTIVE
            lp       = m.get("last_passed_at")
            review   = (mastered and lp is not None
                        and (now - lp) > REVIEW_DAYS * 86400)
            curriculum_out.append({
                **step,
                "index":        i,
                "unlocked":     self.is_unlocked(i),
                "mastered":     mastered,
                "consecutive":  m["consecutive"],
                "best_accuracy": m["best_accuracy"],
                "best_bpm":     m.get("best_bpm", 0.0),
                "attempts":     m["attempts"],
                "needs_review": review,
            })
        return {
            "diagnostic_complete": self._progress["diagnostic_complete"],
            "current_index":       self._progress["current_index"],
            "starting_index":      self._progress["starting_index"],
            "curriculum":          curriculum_out,
            "mastery_accuracy":    MASTERY_ACCURACY,
            "mastery_consecutive": MASTERY_CONSECUTIVE,
            "review_days":         REVIEW_DAYS,
        }

    # ── Import / Export ───────────────────────────────────────────────────────

    def export_progress(self) -> dict:
        """Return the raw progress dict for client-side export."""
        return dict(self._progress)

    def import_progress(self, data: dict) -> bool:
        """
        Overwrite progress from an imported dict.
        Returns False and leaves state unchanged if validation fails.
        """
        if not isinstance(data, dict):
            return False
        if "mastery" not in data:
            return False
        data = self._migrate(data)
        self._progress = data
        self._save()
        return True

    def reset(self):
        self._progress = self._defaults()
        self._save()
