"""Course progression engine.

Manages a sequential curriculum of piano lessons with strict mastery gates:
  - ≥90% accuracy counts as a "pass"
  - 3 consecutive passes → lesson mastered → next lesson unlocked
A diagnostic lesson at the start determines where in the curriculum to begin.
"""

import json
import os
from typing import Dict, List, Optional

MASTERY_ACCURACY    = 90   # minimum accuracy % to count as a pass
MASTERY_CONSECUTIVE = 3    # consecutive passes needed to master a lesson

# Ordered curriculum — every entry is one lesson+hand combination the student
# must master before the next one unlocks.
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
    },

    # ── Etapa 2: Mão Esquerda ────────────────────────────────────────────────
    {
        "lesson_id": "exercises/five_finger_lh",
        "hand":      "left",
        "stage":     "Etapa 2: Mão Esquerda",
        "label":     "Cinco Dedos em Dó (ME)",
    },
    {
        "lesson_id": "scales/c_major_lh",
        "hand":      "left",
        "stage":     "Etapa 2: Mão Esquerda",
        "label":     "Escala de Dó Maior (ME)",
    },

    # ── Etapa 3: Coordenação ─────────────────────────────────────────────────
    {
        "lesson_id": "exercises/contrary_motion_c",
        "hand":      "both",
        "stage":     "Etapa 3: Coordenação",
        "label":     "Movimento Contrário em Dó",
    },
    {
        "lesson_id": "scales/c_major_both",
        "hand":      "both",
        "stage":     "Etapa 3: Coordenação",
        "label":     "Escala de Dó (Ambas as Mãos)",
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
    },
    {
        "lesson_id": "scales/f_major_rh",
        "hand":      "right",
        "stage":     "Etapa 4: Novas Tonalidades",
        "label":     "Escala de Fá Maior",
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
    },

    # ── Etapa 5: Técnica ─────────────────────────────────────────────────────
    {
        "lesson_id": "exercises/hanon_1",
        "hand":      "right",
        "stage":     "Etapa 5: Técnica",
        "label":     "Hanon No. 1",
    },
    {
        "lesson_id": "exercises/alberti_bass",
        "hand":      "left",
        "stage":     "Etapa 5: Técnica",
        "label":     "Baixo Alberti",
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
    },
    {
        "lesson_id": "exercises/broken_chord_c",
        "hand":      "right",
        "stage":     "Etapa 6: Repertório",
        "label":     "Arpejos em Dó",
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
    },
    {
        "lesson_id": "scales/a_major_rh",
        "hand":      "right",
        "stage":     "Etapa 7: Maestria",
        "label":     "Escala de Lá Maior",
    },
    {
        "lesson_id": "exercises/intervals_thirds",
        "hand":      "right",
        "stage":     "Etapa 7: Maestria",
        "label":     "Intervalos: Terças",
    },
    {
        "lesson_id": "scales/chromatic_rh",
        "hand":      "right",
        "stage":     "Etapa 7: Maestria",
        "label":     "Escala Cromática",
    },
    {
        "lesson_id": "songs/bach_prelude_c",
        "hand":      "right",
        "stage":     "Etapa 7: Maestria",
        "label":     "Prelúdio de Bach em Dó",
    },
]


class CourseEngine:
    def __init__(self, progress_file: str = "data/course_progress.json"):
        self._progress_file = progress_file
        self._progress = self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if os.path.exists(self._progress_file):
            try:
                with open(self._progress_file) as f:
                    return json.load(f)
            except Exception:
                pass
        return self._defaults()

    def _defaults(self) -> dict:
        return {
            "diagnostic_complete": False,
            "current_index":  0,
            "starting_index": 0,
            # "{lesson_id}:{hand}" → {consecutive, passes, best_accuracy, attempts}
            "mastery": {},
        }

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
            "consecutive": 0,
            "passes":       0,
            "best_accuracy": 0.0,
            "attempts":     0,
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

    def get_current_step(self) -> Optional[dict]:
        idx = self._progress["current_index"]
        return CURRICULUM[idx] if idx < len(CURRICULUM) else None

    # ── Recording attempts ────────────────────────────────────────────────────

    def record_attempt(self, lesson_id: str, hand: str, accuracy: float) -> dict:
        """Record a completed lesson attempt. Returns a feedback dict."""
        key = self._key(lesson_id, hand)
        m   = self._mastery_data(lesson_id, hand)

        m["attempts"] += 1
        passed = accuracy >= MASTERY_ACCURACY
        if passed:
            m["consecutive"] += 1
            m["passes"]      += 1
        else:
            m["consecutive"] = 0

        if accuracy > m["best_accuracy"]:
            m["best_accuracy"] = accuracy

        self._progress["mastery"][key] = m

        # Diagnostic: auto-complete and choose entry point
        is_diagnostic = lesson_id == "diagnostic/assessment"
        if is_diagnostic and not self._progress["diagnostic_complete"]:
            self._progress["diagnostic_complete"] = True
            m["consecutive"] = MASTERY_CONSECUTIVE   # always pass diagnostic
            self._progress["mastery"][key] = m
            start = self._start_index_from_accuracy(accuracy)
            self._progress["starting_index"] = start
            self._progress["current_index"]  = start

        # Advance current_index when the active lesson is freshly mastered
        newly_mastered = m["consecutive"] >= MASTERY_CONSECUTIVE
        cur = self._progress["current_index"]
        if newly_mastered and cur < len(CURRICULUM):
            step = CURRICULUM[cur]
            if step["lesson_id"] == lesson_id and step["hand"] == hand:
                self._progress["current_index"] = min(cur + 1, len(CURRICULUM))

        self._save()
        return {
            "passed":         passed,
            "newly_mastered": newly_mastered,
            "consecutive":    m["consecutive"],
            "needed":         MASTERY_CONSECUTIVE,
            "accuracy":       accuracy,
            "best_accuracy":  m["best_accuracy"],
            "is_diagnostic":  is_diagnostic,
        }

    def _start_index_from_accuracy(self, acc: float) -> int:
        """Map diagnostic score to curriculum starting index."""
        if acc >= 80:
            return self._first_index_of("Etapa 3: Coordenação")
        if acc >= 60:
            return self._first_index_of("Etapa 2: Mão Esquerda")
        # 0-59%: start from Etapa 1 (index after diagnostic)
        return self._first_index_of("Etapa 1: Mão Direita")

    def _first_index_of(self, stage: str) -> int:
        for i, step in enumerate(CURRICULUM):
            if step["stage"] == stage:
                return i
        return 1  # fallback: skip diagnostic

    # ── State export ──────────────────────────────────────────────────────────

    def get_state(self) -> dict:
        curriculum_out = []
        for i, step in enumerate(CURRICULUM):
            m = self._mastery_data(step["lesson_id"], step["hand"])
            curriculum_out.append({
                **step,
                "index":        i,
                "unlocked":     self.is_unlocked(i),
                "mastered":     m["consecutive"] >= MASTERY_CONSECUTIVE,
                "consecutive":  m["consecutive"],
                "best_accuracy": m["best_accuracy"],
                "attempts":     m["attempts"],
            })
        return {
            "diagnostic_complete": self._progress["diagnostic_complete"],
            "current_index":       self._progress["current_index"],
            "starting_index":      self._progress["starting_index"],
            "curriculum":          curriculum_out,
            "mastery_accuracy":    MASTERY_ACCURACY,
            "mastery_consecutive": MASTERY_CONSECUTIVE,
        }

    def reset(self):
        self._progress = self._defaults()
        self._save()
