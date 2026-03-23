/**
 * Lesson UI: renders the lesson list, manages hint chips, score display,
 * result flash animations, and lesson completion persistence.
 */
const LessonUI = (() => {
  let allLessons     = [];
  let activeCategory = "all";
  let activeLessonId = null;
  let lastState      = null;

  // localStorage key for completed lessons
  const COMPLETED_KEY = "nektar_completed_lessons";

  function _loadCompleted() {
    try {
      return new Set(JSON.parse(localStorage.getItem(COMPLETED_KEY) || "[]"));
    } catch { return new Set(); }
  }

  function _saveCompleted(set) {
    try {
      localStorage.setItem(COMPLETED_KEY, JSON.stringify([...set]));
    } catch {}
  }

  let completedLessons = _loadCompleted();

  function markLessonComplete(lessonId) {
    completedLessons.add(lessonId);
    _saveCompleted(completedLessons);
    _filterAndRender();
  }

  // ── Lesson list ────────────────────────────────────────────────────────────

  function renderList(lessons) {
    allLessons = lessons;
    _filterAndRender();
  }

  function _filterAndRender() {
    const list = document.getElementById("lesson-list");
    list.innerHTML = "";

    const filtered = activeCategory === "all"
      ? allLessons
      : allLessons.filter(l => l.category === activeCategory);

    for (const l of filtered) {
      const el = document.createElement("div");
      const isDone = completedLessons.has(l.id);
      el.className = "lesson-item"
        + (l.id === activeLessonId ? " active" : "")
        + (isDone ? " completed" : "");
      el.dataset.id = l.id;

      const titleEl = document.createElement("div");
      titleEl.className = "lesson-item-title";
      titleEl.textContent = l.title;

      const metaEl = document.createElement("div");
      metaEl.className = "lesson-item-meta";

      const dotsEl = document.createElement("span");
      dotsEl.className = "diff-dots";
      for (let i = 1; i <= 5; i++) {
        const dot = document.createElement("span");
        dot.className = "diff-dot" + (i <= l.difficulty ? " filled" : "");
        dotsEl.appendChild(dot);
      }

      const handEl = document.createElement("span");
      handEl.textContent = " · " + _handLabel(l.hand);

      metaEl.appendChild(dotsEl);
      metaEl.appendChild(handEl);
      el.appendChild(titleEl);
      el.appendChild(metaEl);

      el.addEventListener("click", () => selectLesson(l));
      list.appendChild(el);
    }
  }

  function selectLesson(lesson) {
    activeLessonId = lesson.id;
    _filterAndRender();

    document.getElementById("lesson-title").textContent = lesson.title;
    document.getElementById("lesson-desc").textContent  = lesson.description;

    const badges = document.getElementById("lesson-badges");
    badges.innerHTML = "";
    const SAFE_CATS = new Set(["scales", "exercises", "chords", "songs", "trainer"]);
    const catBadge = document.createElement("span");
    catBadge.className = "badge" + (SAFE_CATS.has(lesson.category) ? ` cat-${lesson.category}` : "");
    catBadge.textContent = _catLabel(lesson.category);
    const handBadge = document.createElement("span");
    handBadge.className = "badge";
    handBadge.textContent = _handLabel(lesson.hand);
    badges.appendChild(catBadge);
    badges.appendChild(handBadge);

    document.getElementById("btn-reference").disabled = false;
    document.getElementById("btn-start").disabled     = false;
    document.getElementById("btn-stop").disabled      = true;

    resetScore();
    updateHint(null);
    updateNextNotes([]);

    return lesson;
  }

  function addImportedLesson(summary) {
    allLessons = allLessons.filter(l => !l.id.startsWith("midi/"));
    allLessons.unshift(summary);
    selectLesson(summary);
    _filterAndRender();
  }

  // ── Category tabs ──────────────────────────────────────────────────────────

  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("category-tabs").addEventListener("click", (e) => {
      const btn = e.target.closest(".cat-btn");
      if (!btn) return;
      document.querySelectorAll(".cat-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeCategory = btn.dataset.cat;
      _filterAndRender();
    });
  });

  // ── Score ──────────────────────────────────────────────────────────────────

  function updateScore(state) {
    lastState = state;
    const s     = state.score;
    const total = state.total_steps;
    const step  = state.current_step;

    document.getElementById("score-correct").textContent = `✓ ${s.correct}`;
    document.getElementById("score-wrong").textContent   = `✗ ${s.wrong}`;
    document.getElementById("score-step").textContent    = `${step} / ${total}`;

    const pct = total > 0 && step > 0
      ? Math.round((s.correct / total) * 100) + "%" : "—";
    document.getElementById("score-pct").textContent = pct;

    const fill = total > 0 ? (step / total) * 100 : 0;
    document.getElementById("progress-fill").style.width = fill + "%";

    // Loop markers
    _updateLoopMarkers(state);

    // Auto-speed streak badge
    const streakEl = document.getElementById("auto-speed-streak");
    if (state.auto_speed && state.auto_speed_streak > 0) {
      streakEl.textContent = `🔥 ${state.auto_speed_streak}`;
      streakEl.classList.remove("hidden");
    } else {
      streakEl.classList.add("hidden");
    }

    // Auto-speed toggle sync
    const autoToggle = document.getElementById("auto-speed-toggle");
    if (autoToggle && autoToggle.checked !== state.auto_speed) {
      autoToggle.checked = state.auto_speed;
    }
  }

  function _updateLoopMarkers(state) {
    const track  = document.getElementById("progress-track");
    const startM = document.getElementById("loop-start-marker");
    const endM   = document.getElementById("loop-end-marker");
    const badge  = document.getElementById("loop-badge");
    const clearB = document.getElementById("btn-clear-loop");

    if (!startM || !endM) return;

    if (state.loop_start !== null && state.loop_end !== null) {
      const total = state.total_steps || 1;
      const startPct = (state.loop_start / total) * 100;
      const endPct   = (state.loop_end   / total) * 100;
      startM.style.left = startPct + "%";
      endM.style.left   = endPct   + "%";
      startM.classList.remove("hidden");
      endM.classList.remove("hidden");
      badge.classList.remove("hidden");
      clearB.classList.remove("hidden");
    } else {
      startM.classList.add("hidden");
      endM.classList.add("hidden");
      badge.classList.add("hidden");
      clearB.classList.add("hidden");
    }
  }

  function resetScore() {
    document.getElementById("score-correct").textContent = "✓ 0";
    document.getElementById("score-wrong").textContent   = "✗ 0";
    document.getElementById("score-step").textContent    = "0 / 0";
    document.getElementById("score-pct").textContent     = "—";
    document.getElementById("progress-fill").style.width = "0%";

    const streakEl = document.getElementById("auto-speed-streak");
    if (streakEl) streakEl.classList.add("hidden");
  }

  // ── Hint area ──────────────────────────────────────────────────────────────

  let chipCache = new Map();  // midi → chip element

  function updateHint(expectedNotes, fingeringMap) {
    const label = document.getElementById("hint-label");
    const chips = document.getElementById("hint-notes");

    chipCache = new Map();

    if (!expectedNotes || expectedNotes.length === 0) {
      label.textContent = "Select a lesson and press Start";
      chips.innerHTML = "";
      return;
    }

    label.textContent = expectedNotes.length === 1 ? "Play this note:" : "Play these notes:";
    chips.innerHTML = "";
    for (const midi of expectedNotes) {
      const chip = document.createElement("div");
      chip.className = "hint-note-chip";
      chip.dataset.midi = midi;

      const nameEl = document.createElement("span");
      nameEl.textContent = Keyboard.noteName(midi);
      chip.appendChild(nameEl);

      // Fingering sub-label
      const finger = fingeringMap && fingeringMap[String(midi)];
      if (finger) {
        const fEl = document.createElement("span");
        fEl.className = "finger-num";
        fEl.textContent = `Finger ${finger}`;
        chip.appendChild(fEl);
      }

      chips.appendChild(chip);
      chipCache.set(midi, chip);
    }
  }

  function updateNextNotes(nextNotes) {
    const preview = document.getElementById("next-notes-preview");
    const container = document.getElementById("next-notes");
    if (!preview || !container) return;

    if (!nextNotes || nextNotes.length === 0) {
      preview.classList.add("hidden");
      return;
    }

    preview.classList.remove("hidden");
    container.innerHTML = "";
    for (const midi of nextNotes) {
      const chip = document.createElement("span");
      chip.className = "next-note-chip";
      chip.textContent = Keyboard.noteName(midi);
      container.appendChild(chip);
    }
  }

  function markChipPressed(midi, on) {
    const chip = chipCache.get(midi);
    if (chip) chip.classList.toggle("pressed", on);
  }

  // ── Result flash ───────────────────────────────────────────────────────────

  function flashResult(type) {
    const el = document.getElementById("result-flash");
    el.className = "";
    el.textContent = type === "correct" ? "✓" : "✗";
    void el.offsetWidth;  // force reflow
    el.classList.add(type === "correct" ? "show-correct" : "show-wrong");
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  function _handLabel(hand) {
    return { right: "Right hand", left: "Left hand", both: "Both hands" }[hand] || hand;
  }

  function _catLabel(cat) {
    return {
      scales: "Scale", exercises: "Exercise", chords: "Chord",
      songs: "Song", trainer: "Trainer",
    }[cat] || cat;
  }

  function getActiveLessonId() { return activeLessonId; }
  function getAllLessons()     { return allLessons; }

  return {
    renderList,
    selectLesson,
    addImportedLesson,
    updateScore,
    resetScore,
    updateHint,
    updateNextNotes,
    markChipPressed,
    flashResult,
    getActiveLessonId,
    getAllLessons,
    markLessonComplete,
  };
})();
