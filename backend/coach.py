"""
Coach — analyses lesson attempt data and returns personalised technique tips
in Portuguese.

Call get_tips(context) where context is a dict built by websocket_server after
each lesson_complete event.
"""

from typing import Dict, List, Optional

# ── Note name helpers ─────────────────────────────────────────────────────────

_NAMES_PT = ["Dó", "Dó#", "Ré", "Ré#", "Mi", "Fá",
             "Fá#", "Sol", "Sol#", "Lá", "Lá#", "Si"]
_BLACK_SEMITONES = {1, 3, 6, 8, 10}


def _note_name(midi: int) -> str:
    octave = midi // 12 - 1
    return f"{_NAMES_PT[midi % 12]}{octave}"


def _is_black(midi: int) -> bool:
    return (midi % 12) in _BLACK_SEMITONES


# ── Category tips library ─────────────────────────────────────────────────────

_TIPS: Dict[str, Dict[str, str]] = {
    "scales": {
        "slow_down":
            "Reduz o BPM para 40 e trabalha grupos de 4 notas de cada vez, "
            "só aumentando quando tocas sem hesitar.",
        "thumb_crossing":
            "O cruzamento do polegar é o ponto mais difícil das escalas. "
            "Pratica a transição polegar→dedo3 em loop, muito devagar, "
            "até o movimento ser automático.",
        "curved_fingers":
            "Mantém os dedos curvados como se abraçasses uma bola. "
            "Toca com a ponta (não a polpa) de cada dedo.",
        "evenness":
            "Grava-te a tocar e ouve se todas as notas têm o mesmo volume. "
            "Dedos mais fracos (3, 4, 5) precisam de exercício extra.",
        "black_keys":
            "Antes de tocar a escala completa, pratica só as notas pretas "
            "da escala, depois integra as brancas.",
    },
    "exercises": {
        "slow_down":
            "Baixa o BPM para metade e foca-te na qualidade de cada nota, "
            "não na velocidade.",
        "finger_independence":
            "Mantém os dedos que não estão a tocar levantados mas relaxados. "
            "A independência constrói-se com repetição lenta.",
        "relaxation":
            "Se sentires tensão na mão ou antebraço, para, agita o pulso "
            "suavemente e recomeça mais devagar. Tensão é o inimigo da técnica.",
        "hand_position":
            "Mantém o pulso ao nível das teclas (não acima, não abaixo) "
            "e o cotovelo ligeiramente dobrado.",
        "alberti_hint":
            "No baixo Alberti (raiz–5ª–3ª–5ª), pratica cada intervalo "
            "isoladamente antes de os encadear.",
        "hanon_hint":
            "No Hanon, cada posição deve soar idêntica à anterior. "
            "Se uma posição soa pior, repete-a 3× antes de avançar.",
    },
    "chords": {
        "simultaneous":
            "Para o acorde soar limpo, todas as teclas devem descer em simultâneo. "
            "Pratica 'largar' a mão inteira de uma só vez sobre as teclas.",
        "fingering":
            "Memoriza a digitação do acorde antes de olhar para o teclado. "
            "Com a mão no colo, reproduz a forma do acorde no ar.",
        "wrist":
            "Usa o peso do braço, não a força dos dedos. "
            "O pulso relaxado permite transições mais suaves entre acordes.",
        "position_memory":
            "Marca visualmente a posição de cada acorde no teclado antes de tocar. "
            "A memória espacial é mais fiável do que contar intervalos.",
    },
    "songs": {
        "hands_separate":
            "Domina cada mão separadamente ao BPM alvo antes de as juntar. "
            "Juntar mãos antes de tempo é a causa nº1 de bloqueios.",
        "identify_hard_bars":
            "Identifica os 1-2 compassos mais difíceis e usa o Loop para os "
            "praticar isoladamente até soarem fluídos.",
        "listen_first":
            "Antes de tentar, ouve a referência (▶ Reference) 2-3 vezes "
            "com atenção. O ouvido guia os dedos.",
        "rhythm_first":
            "Toca as notas no ritmo correto mesmo que algumas estejam erradas. "
            "O ritmo é mais difícil de corrigir depois do que as notas.",
        "slow_bpm":
            "Baixa o BPM para um andamento em que tocas sem hesitar, "
            "mesmo que seja muito lento. A velocidade vem com repetição.",
    },
    "diagnostic": {
        "relax":
            "É apenas uma avaliação inicial — não há resposta errada permanente. "
            "Toca o que sabes e a app ajusta o percurso.",
    },
    "trainer": {
        "geography":
            "Para melhorar a localização das notas, pratica nomear as teclas "
            "em voz alta enquanto as tocas, sem olhar para o teclado.",
    },
}

# Tips that apply regardless of category
_GENERAL_TIPS: Dict[str, str] = {
    "bpm_too_high":
        "O andamento está demasiado rápido para esta fase. "
        "Baixa o BPM até conseguires 3 passes sem erros, depois sobe 5 BPM de cada vez.",
    "use_drill":
        "Experimenta o modo Drill — quando erras, o acorde reinicia e podes "
        "corrigi-lo imediatamente sem avançar.",
    "use_loop":
        "Usa a função Loop (botão '[ Loop ]') para isolar a secção onde erras mais "
        "e praticá-la em repetição.",
    "take_break":
        "Após 5+ tentativas seguidas sem progresso, faz uma pausa de 5-10 min. "
        "A memória muscular consolida-se durante o descanso — não na fadiga.",
    "listen_reference":
        "Ouve a referência (▶ Reference) antes de tentar. "
        "Ter a melodia interiorizada facilita muito a execução.",
    "consistent_black_keys":
        "Estás a errar consistentemente notas pretas (teclas elevadas). "
        "Pratica localizar essas notas de olhos fechados antes de continuar.",
    "most_wrong_note":
        "A nota {note} é aquela que erras mais nesta lição. "
        "Pratica encontrá-la rapidamente no teclado, sozinha, 10× seguidas.",
    "both_hands_separate":
        "Para lições com ambas as mãos, domina cada mão separadamente primeiro — "
        "mesmo que já conheças a lição.",
}


# ── Public API ────────────────────────────────────────────────────────────────

def get_tips(context: dict) -> List[str]:
    """
    Return a list of 2–4 personalised coaching tips in Portuguese.

    Expected context keys:
      category        str   — lesson category (scales, songs, exercises, chords…)
      accuracy        float — completion accuracy 0–100
      bpm             float — BPM at which the attempt was made
      min_bpm         float|None — minimum BPM required for mastery (if set)
      wrong_note_counts dict  — {midi_note: count} for notes pressed incorrectly
      consecutive_fails int  — how many consecutive non-passes
      attempts        int   — total attempts on this lesson
      hand            str   — right | left | both
    """
    tips: List[str] = []
    cat          = context.get("category", "")
    accuracy     = float(context.get("accuracy", 0))
    bpm          = float(context.get("bpm", 60))
    min_bpm      = context.get("min_bpm")
    wrong_counts = context.get("wrong_note_counts", {}) or {}
    consec_fails = int(context.get("consecutive_fails", 0))
    attempts     = int(context.get("attempts", 0))
    hand         = context.get("hand", "right")

    cat_tips = _TIPS.get(cat, {})

    # ── BPM gate ─────────────────────────────────────────────────────────────
    if min_bpm and bpm < min_bpm * 0.85:
        tips.append(_GENERAL_TIPS["bpm_too_high"])

    # ── Take-a-break threshold ────────────────────────────────────────────────
    if attempts >= 5 and consec_fails >= 3:
        tips.append(_GENERAL_TIPS["take_break"])
        # After a break suggestion, fewer tips are useful
        tips += _pick_category_tips(cat_tips, accuracy, 1)
        return tips[:4]

    # ── Accuracy-based general advice ────────────────────────────────────────
    if accuracy < 50:
        if "slow_down" in cat_tips:
            tips.append(cat_tips["slow_down"])
        else:
            tips.append(_GENERAL_TIPS["bpm_too_high"])

    if consec_fails >= 2:
        tips.append(_GENERAL_TIPS["use_drill"])

    # ── Wrong note pattern analysis ───────────────────────────────────────────
    if wrong_counts:
        # Most-missed note
        most_wrong_midi = max(wrong_counts, key=lambda k: wrong_counts[k])
        if wrong_counts[most_wrong_midi] >= 2:
            note_str = _note_name(most_wrong_midi)
            tips.append(_GENERAL_TIPS["most_wrong_note"].format(note=note_str))

        # Majority of wrong notes are black keys?
        black_wrong = sum(v for k, v in wrong_counts.items() if _is_black(k))
        total_wrong = sum(wrong_counts.values())
        if total_wrong >= 3 and black_wrong / total_wrong >= 0.6:
            tips.append(_GENERAL_TIPS["consistent_black_keys"])

    # ── Both-hands tip ────────────────────────────────────────────────────────
    if hand == "both" and accuracy < 75:
        tips.append(_GENERAL_TIPS["both_hands_separate"])

    # ── Category-specific tips ────────────────────────────────────────────────
    tips += _pick_category_tips(cat_tips, accuracy, needed=max(0, 4 - len(tips)))

    # ── Loop suggestion for medium-accuracy failures ──────────────────────────
    if 40 <= accuracy < 80 and len(tips) < 4:
        tips.append(_GENERAL_TIPS["use_loop"])

    # ── Listen to reference if early attempts ────────────────────────────────
    if attempts <= 2 and accuracy < 70 and len(tips) < 4:
        tips.append(_GENERAL_TIPS["listen_reference"])

    # Deduplicate while preserving order, cap at 4
    seen = set()
    unique: List[str] = []
    for t in tips:
        if t not in seen:
            seen.add(t)
            unique.append(t)

    return unique[:4]


def _pick_category_tips(cat_tips: dict, accuracy: float, needed: int) -> List[str]:
    """Select the most relevant category-specific tips given accuracy."""
    if needed <= 0 or not cat_tips:
        return []

    # Priority order within each category (first = most important)
    priority_keys = {
        "scales":     ["thumb_crossing", "curved_fingers", "evenness", "black_keys"],
        "exercises":  ["finger_independence", "relaxation", "hand_position",
                       "alberti_hint", "hanon_hint"],
        "chords":     ["simultaneous", "fingering", "wrist", "position_memory"],
        "songs":      ["identify_hard_bars", "rhythm_first", "hands_separate",
                       "slow_bpm", "listen_first"],
        "trainer":    ["geography"],
        "diagnostic": ["relax"],
    }

    # Find matching priority list
    selected: List[str] = []
    for key in list(cat_tips.keys()):
        # Use priority order if available
        break
    for key in _get_priority(cat_tips):
        if key in cat_tips and len(selected) < needed:
            selected.append(cat_tips[key])

    return selected


def _get_priority(cat_tips: dict) -> List[str]:
    """Return keys of cat_tips in a sensible priority order."""
    # Just return keys as-is; the dict insertion order reflects priority
    # in the _TIPS definition above.
    return list(cat_tips.keys())
