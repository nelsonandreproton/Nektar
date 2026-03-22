/**
 * Lesson UI: renders the lesson list, manages hint chips, score display,
 * and result flash animations.
 */
const LessonUI = (() => {
  let allLessons = [];
  let activeCategory = "all";
  let activeLessonId = null;
  let lastState = null;

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
      el.className = "lesson-item" + (l.id === activeLessonId ? " active" : "");
      el.dataset.id = l.id;

      const titleEl = document.createElement("div");
      titleEl.className = "lesson-item-title";
      titleEl.textContent = l.title;  // textContent prevents XSS

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
    const SAFE_CATS = new Set(["scales", "exercises", "chords", "songs"]);
    const catBadge = document.createElement("span");
    catBadge.className = "badge" + (SAFE_CATS.has(lesson.category) ? ` cat-${lesson.category}` : "");
    catBadge.textContent = _catLabel(lesson.category);
    const handBadge = document.createElement("span");
    handBadge.className = "badge";
    handBadge.textContent = _handLabel(lesson.hand);
    badges.appendChild(catBadge);
    badges.appendChild(handBadge);

    document.getElementById("btn-reference").disabled = false;
    document.getElementById("btn-start").disabled = false;
    document.getElementById("btn-stop").disabled = true;

    resetScore();
    updateHint(null);

    return lesson;
  }

  function addImportedLesson(summary) {
    // Remove previous import if it has the same id
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
    const s = state.score;
    const total = state.total_steps;
    const step  = state.current_step;

    document.getElementById("score-correct").textContent = `✓ ${s.correct}`;
    document.getElementById("score-wrong").textContent   = `✗ ${s.wrong}`;
    document.getElementById("score-step").textContent    = `${step} / ${total}`;

    const pct = total > 0 && step > 0
      ? Math.round((s.correct / step) * 100) + "%" : "—";
    document.getElementById("score-pct").textContent = pct;

    const fill = total > 0 ? (step / total) * 100 : 0;
    document.getElementById("progress-fill").style.width = fill + "%";
  }

  function resetScore() {
    document.getElementById("score-correct").textContent = "✓ 0";
    document.getElementById("score-wrong").textContent   = "✗ 0";
    document.getElementById("score-step").textContent    = "0 / 0";
    document.getElementById("score-pct").textContent     = "—";
    document.getElementById("progress-fill").style.width = "0%";
  }

  // ── Hint area ──────────────────────────────────────────────────────────────

  let chipCache = new Map();  // midi → chip element

  function updateHint(expectedNotes) {
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
      chip.textContent = Keyboard.noteName(midi);
      chips.appendChild(chip);
      chipCache.set(midi, chip);
    }
  }

  function markChipPressed(midi, on) {
    const chip = chipCache.get(midi);
    if (chip) chip.classList.toggle("pressed", on);
  }

  // ── Result flash ───────────────────────────────────────────────────────────

  function flashResult(type) {
    const el = document.getElementById("result-flash");
    el.className = "";          // reset
    el.textContent = type === "correct" ? "✓" : "✗";
    void el.offsetWidth;        // force reflow
    el.classList.add(type === "correct" ? "show-correct" : "show-wrong");
  }

  // ── Helpers ────────────────────────────────────────────────────────────────

  function _handLabel(hand) {
    return { right: "Right hand", left: "Left hand", both: "Both hands" }[hand] || hand;
  }

  function _catLabel(cat) {
    return { scales: "Scale", exercises: "Exercise", chords: "Chord", songs: "Song" }[cat] || cat;
  }

  function getActiveLessonId() { return activeLessonId; }

  return {
    renderList,
    selectLesson,
    addImportedLesson,
    updateScore,
    resetScore,
    updateHint,
    markChipPressed,
    flashResult,
    getActiveLessonId,
  };
})();
