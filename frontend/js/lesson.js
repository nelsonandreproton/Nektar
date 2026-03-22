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

      const dots = [1,2,3,4,5].map(i =>
        `<span class="diff-dot${i <= l.difficulty ? " filled" : ""}"></span>`
      ).join("");

      el.innerHTML = `
        <div class="lesson-item-title">${l.title}</div>
        <div class="lesson-item-meta">
          <span class="diff-dots">${dots}</span>
          <span> · ${_handLabel(l.hand)}</span>
        </div>
      `;
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
    badges.innerHTML = `
      <span class="badge cat-${lesson.category}">${_catLabel(lesson.category)}</span>
      <span class="badge">${_handLabel(lesson.hand)}</span>
    `;

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

  let hintMidiSet = new Set();

  function updateHint(expectedNotes) {
    const label = document.getElementById("hint-label");
    const chips = document.getElementById("hint-notes");

    hintMidiSet = new Set(expectedNotes || []);

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
    }
  }

  function markChipPressed(midi, on) {
    const chip = document.querySelector(`.hint-note-chip[data-midi="${midi}"]`);
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
