/**
 * app.js — main controller.
 * Wires WebSocket events → Keyboard + LessonUI, and UI controls → WebSocket.
 */
document.addEventListener("DOMContentLoaded", () => {

  // ── State ──────────────────────────────────────────────────────────────────
  let currentHand     = "right";
  let currentBpm      = 60;
  let currentMode     = "wait";
  let lessonStatus    = "idle";   // idle | playing | completed
  let loopPending     = false;    // waiting to set loop end on next press
  let loopStartStep   = null;
  let courseMode      = false;    // true when Course tab is active

  // ── WebSocket lifecycle ────────────────────────────────────────────────────

  window.addEventListener("ws:open", () => {
    WS.send({ type: "get_devices" });
    WS.send({ type: "get_lessons" });
    WS.send({ type: "get_course" });
  });

  window.addEventListener("ws:close", () => {
    document.getElementById("device-status").className = "status-dot disconnected";
    document.getElementById("device-label").textContent = "Not connected";
  });

  // ── Devices ────────────────────────────────────────────────────────────────

  window.addEventListener("ws:devices", (e) => {
    const { inputs } = e.detail;
    const sel = document.getElementById("device-select");
    sel.innerHTML = '<option value="">— select MIDI device —</option>';
    for (const name of inputs) {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      if (name.toLowerCase().includes("nektar")) opt.selected = true;
      sel.appendChild(opt);
    }
    if (sel.value) connectDevice(sel.value);
  });

  window.addEventListener("ws:device_connected", (e) => {
    document.getElementById("device-status").className = "status-dot connected";
    document.getElementById("device-label").textContent = e.detail.name || "Connected";
  });

  window.addEventListener("ws:device_disconnected", () => {
    document.getElementById("device-status").className = "status-dot disconnected";
    document.getElementById("device-label").textContent = "Not connected";
  });

  document.getElementById("device-select").addEventListener("change", (e) => {
    if (e.target.value) connectDevice(e.target.value);
  });

  document.getElementById("btn-refresh-devices").addEventListener("click", () => {
    WS.send({ type: "get_devices" });
  });

  function connectDevice(name) {
    WS.send({ type: "connect_device", name });
  }

  // ── Lessons list ───────────────────────────────────────────────────────────

  window.addEventListener("ws:lessons", (e) => {
    LessonUI.renderList(e.detail.lessons);
  });

  window.addEventListener("ws:lesson_loaded", (e) => {
    LessonUI.addImportedLesson(e.detail.summary);
    document.getElementById("btn-start").disabled     = false;
    document.getElementById("btn-reference").disabled = false;
  });

  // ── Course events ───────────────────────────────────────────────────────────

  CourseUI.init((lessonId, hand) => {
    // User clicked a course step — select that lesson and set hand
    const allLessons = LessonUI.getAllLessons();
    const lesson     = allLessons.find(l => l.id === lessonId);
    if (lesson) {
      LessonUI.selectLesson(lesson);
    }
    // Set the hand selector to match the curriculum's required hand
    currentHand = hand;
    document.querySelectorAll(".seg-btn[data-hand]").forEach(b =>
      b.classList.toggle("active", b.dataset.hand === hand)
    );
    WS.send({ type: "set_hand", hand });
    document.getElementById("btn-start").disabled     = false;
    document.getElementById("btn-reference").disabled = false;
  });

  window.addEventListener("ws:course_state", (e) => {
    CourseUI.render(e.detail.course);
    _syncCourseWelcome(e.detail.course);
  });

  window.addEventListener("ws:course_attempt", (e) => {
    CourseUI.showAttemptFeedback(e.detail.feedback);
    CourseUI.render(e.detail.course);
    // If newly mastered, auto-select next lesson in course mode
    if (courseMode && e.detail.feedback.newly_mastered) {
      const nextStep = e.detail.course.curriculum[e.detail.course.current_index];
      if (nextStep) {
        setTimeout(() => _selectCourseStep(nextStep, e.detail.course), 800);
      }
    }
  });

  function _selectCourseStep(step, courseState) {
    const allLessons = LessonUI.getAllLessons();
    const lesson = allLessons.find(l => l.id === step.lesson_id);
    if (lesson) LessonUI.selectLesson(lesson);
    currentHand = step.hand;
    document.querySelectorAll(".seg-btn[data-hand]").forEach(b =>
      b.classList.toggle("active", b.dataset.hand === step.hand)
    );
    WS.send({ type: "set_hand", hand: step.hand });
    document.getElementById("btn-start").disabled     = false;
    document.getElementById("btn-reference").disabled = false;
  }

  function _syncCourseWelcome(courseState) {
    if (!courseState) return;
    if (!courseState.diagnostic_complete && courseMode) {
      // Auto-select the diagnostic lesson
      const diagStep = courseState.curriculum[0];
      if (diagStep) _selectCourseStep(diagStep, courseState);
    }
  }

  // Course tab toggle
  document.getElementById("btn-course-tab").addEventListener("click", () => {
    courseMode = true;
    document.getElementById("lesson-list").classList.add("hidden");
    document.getElementById("course-panel").classList.remove("hidden");
    document.querySelectorAll(".cat-btn").forEach(b =>
      b.classList.toggle("active", b === document.getElementById("btn-course-tab"))
    );
    WS.send({ type: "get_course" });
  });

  // When any non-course category tab is clicked, hide course panel
  document.querySelectorAll(".cat-btn:not(#btn-course-tab)").forEach(btn => {
    btn.addEventListener("click", () => {
      courseMode = false;
      document.getElementById("lesson-list").classList.remove("hidden");
      document.getElementById("course-panel").classList.add("hidden");
    });
  });

  // Reset course button
  document.getElementById("btn-reset-course").addEventListener("click", () => {
    if (confirm("Tens a certeza que queres apagar todo o progresso do curso?")) {
      WS.send({ type: "reset_course" });
    }
  });

  // ── MIDI input events ──────────────────────────────────────────────────────

  window.addEventListener("ws:note_on", (e) => {
    const { note, result, velocity } = e.detail;
    Keyboard.setState(note, "pressed", true);
    Keyboard.setVelocity(note, velocity || 80);
    LessonUI.markChipPressed(note, true);

    if (result === "correct") {
      Keyboard.flashCorrect(note);
      LessonUI.flashResult("correct");
    } else if (result === "wrong") {
      Keyboard.flashWrong(note);
      LessonUI.flashResult("wrong");
    }
  });

  window.addEventListener("ws:note_off", (e) => {
    const { note } = e.detail;
    Keyboard.setState(note, "pressed", false);
    LessonUI.markChipPressed(note, false);
  });

  // ── Sustain pedal ──────────────────────────────────────────────────────────

  window.addEventListener("ws:pedal", (e) => {
    const { on } = e.detail;
    const indicator = document.getElementById("pedal-indicator");
    if (indicator) {
      indicator.textContent = on ? "⬛ Pedal ↓" : "⬛ Pedal";
      indicator.classList.toggle("pedal-on", on);
    }
  });

  // ── Lesson state updates ───────────────────────────────────────────────────

  window.addEventListener("ws:lesson_state", (e) => {
    applyState(e.detail.state);
  });

  window.addEventListener("ws:lesson_complete", (e) => {
    const score = e.detail.score;
    lessonStatus = "completed";

    Keyboard.clearAll();
    LessonUI.updateHint(null);
    LessonUI.updateNextNotes([]);
    StaffView.update([]);

    const pct   = score.total > 0 ? Math.round((score.correct / score.total) * 100) : 0;
    const emoji = pct === 100 ? "🎉" : pct >= 80 ? "🎹" : "👍";
    document.getElementById("hint-label").textContent =
      `${emoji} Completo! Precisão: ${pct}%  (${score.correct}/${score.total} correctas)`;

    document.getElementById("btn-stop").disabled  = true;
    document.getElementById("btn-start").disabled = false;

    // Persist completion
    const lessonId = LessonUI.getActiveLessonId();
    if (pct >= 70 && lessonId) {
      LessonUI.markLessonComplete(lessonId);
    }

    // Record session stats
    Session.recordResult(score.correct, score.wrong);
  });

  function applyState(state) {
    if (!state) return;
    lessonStatus = state.status;

    // Update hint + expected keys
    const expected   = state.current_expected   || [];
    const fingering  = state.current_fingering  || {};
    const nextNotes  = state.next_notes         || [];

    Keyboard.setExpected(expected);
    Keyboard.setFingering(fingering);
    LessonUI.updateHint(expected.length > 0 ? expected : null, fingering);
    LessonUI.updateNextNotes(nextNotes);
    LessonUI.updateScore(state);

    // Update staff view
    StaffView.update(expected);

    // Sync BPM slider
    if (state.bpm !== undefined && state.bpm !== currentBpm) {
      currentBpm = state.bpm;
      document.getElementById("bpm-slider").value        = Math.round(currentBpm);
      document.getElementById("bpm-display").textContent = Math.round(currentBpm);
    }

    // Sync hand buttons
    if (state.hand && state.hand !== currentHand) {
      currentHand = state.hand;
      document.querySelectorAll(".seg-btn[data-hand]").forEach(b => {
        b.classList.toggle("active", b.dataset.hand === currentHand);
      });
    }

    // Sync mode buttons
    if (state.mode && state.mode !== currentMode) {
      currentMode = state.mode;
      document.querySelectorAll(".seg-btn[data-mode]").forEach(b => {
        b.classList.toggle("active", b.dataset.mode === currentMode);
      });
    }

    // Sync auto-speed toggle
    const autoToggle = document.getElementById("auto-speed-toggle");
    if (autoToggle && autoToggle.checked !== state.auto_speed) {
      autoToggle.checked = state.auto_speed;
    }

    // Button visibility
    const playing = state.status === "playing";
    document.getElementById("btn-stop").disabled  = !playing;
    document.getElementById("btn-start").disabled = playing;
    document.getElementById("btn-set-loop").disabled = !playing;
  }

  // ── Playback events ────────────────────────────────────────────────────────

  window.addEventListener("ws:playback_note_on", (e) => {
    Keyboard.setState(e.detail.note, "playback", true);
  });
  window.addEventListener("ws:playback_note_off", (e) => {
    Keyboard.setState(e.detail.note, "playback", false);
  });

  // ── Controls ───────────────────────────────────────────────────────────────

  document.getElementById("btn-start").addEventListener("click", () => {
    const id = LessonUI.getActiveLessonId();
    if (!id) return;
    Keyboard.clearAll();
    LessonUI.resetScore();
    loopPending   = false;
    loopStartStep = null;
    document.getElementById("course-feedback").classList.add("hidden");
    WS.send({ type: "start_lesson", lesson_id: id, hand: currentHand });
    CourseUI.setActiveLessonId(id, currentHand);
    Session.startTimer();
    Session.recordLessonPlayed(id);
  });

  document.getElementById("btn-stop").addEventListener("click", () => {
    WS.send({ type: "stop_lesson" });
    WS.send({ type: "stop_reference" });
    Keyboard.clearAll();
    LessonUI.updateHint(null);
    LessonUI.updateNextNotes([]);
    StaffView.update([]);
    loopPending   = false;
    loopStartStep = null;
  });

  document.getElementById("btn-reference").addEventListener("click", () => {
    WS.send({ type: "play_reference", hand: currentHand, bpm: currentBpm });
  });

  // Hand selector
  document.getElementById("hand-btns").addEventListener("click", (e) => {
    const btn = e.target.closest(".seg-btn[data-hand]");
    if (!btn) return;
    currentHand = btn.dataset.hand;
    document.querySelectorAll(".seg-btn[data-hand]").forEach(b =>
      b.classList.toggle("active", b.dataset.hand === currentHand)
    );
    WS.send({ type: "set_hand", hand: currentHand });
  });

  // Mode selector (wait / drill)
  document.getElementById("mode-btns").addEventListener("click", (e) => {
    const btn = e.target.closest(".seg-btn[data-mode]");
    if (!btn) return;
    currentMode = btn.dataset.mode;
    document.querySelectorAll(".seg-btn[data-mode]").forEach(b =>
      b.classList.toggle("active", b.dataset.mode === currentMode)
    );
    WS.send({ type: "set_mode", mode: currentMode });
  });

  // BPM slider
  const bpmSlider  = document.getElementById("bpm-slider");
  const bpmDisplay = document.getElementById("bpm-display");
  bpmSlider.addEventListener("input", () => {
    currentBpm = parseInt(bpmSlider.value);
    bpmDisplay.textContent = currentBpm;
    WS.send({ type: "set_bpm", bpm: currentBpm });
  });

  // Auto-speed toggle
  document.getElementById("auto-speed-toggle").addEventListener("change", (e) => {
    WS.send({ type: "set_auto_speed", enabled: e.target.checked });
  });

  // ── Loop section ───────────────────────────────────────────────────────────

  document.getElementById("btn-set-loop").addEventListener("click", _handleLoopBtn);
  document.getElementById("btn-clear-loop").addEventListener("click", () => {
    WS.send({ type: "clear_loop" });
    loopPending   = false;
    loopStartStep = null;
    document.getElementById("btn-set-loop").textContent = "[ Loop ]";
  });

  function _handleLoopBtn() {
    if (lessonStatus !== "playing") return;
    // We read current step from the most recent state via score bar
    const stepText = document.getElementById("score-step").textContent;
    const match    = stepText.match(/^(\d+)\s*\/\s*(\d+)/);
    if (!match) return;
    const currentStep = parseInt(match[1]);

    if (!loopPending) {
      // First press: mark start
      loopStartStep = currentStep;
      loopPending   = true;
      document.getElementById("btn-set-loop").textContent = "[ End ]";
    } else {
      // Second press: set end
      if (loopStartStep !== null && currentStep > loopStartStep) {
        WS.send({ type: "set_loop", start: loopStartStep, end: currentStep });
      }
      loopPending   = false;
      loopStartStep = null;
      document.getElementById("btn-set-loop").textContent = "[ Loop ]";
    }
  }

  // ── MIDI file import ───────────────────────────────────────────────────────

  document.getElementById("midi-file-input").addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const MAX_BYTES = 10 * 1024 * 1024;
    if (file.size > MAX_BYTES) {
      alert(`File too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum is 10 MB.`);
      e.target.value = "";
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      const bytes  = new Uint8Array(reader.result);
      const binary = bytes.reduce((acc, b) => acc + String.fromCharCode(b), "");
      WS.send({
        type:     "load_midi",
        filename: file.name,
        content:  btoa(binary),
      });
    };
    reader.readAsArrayBuffer(file);
    e.target.value = "";
  });

  // ── Error notifications ────────────────────────────────────────────────────

  window.addEventListener("ws:error", (e) => {
    console.warn("[Server error]", e.detail.message);
    const label = document.getElementById("hint-label");
    const prev  = label.textContent;
    label.style.color = "var(--red)";
    label.textContent = "⚠ " + e.detail.message;
    setTimeout(() => {
      label.style.color = "";
      label.textContent = prev;
    }, 3000);
  });

  // ── Metronome panel ────────────────────────────────────────────────────────

  const metroPanel = document.getElementById("metronome-panel");
  document.getElementById("btn-metronome").addEventListener("click", () => {
    metroPanel.classList.toggle("hidden");
  });
  document.getElementById("btn-metro-close").addEventListener("click", () => {
    metroPanel.classList.add("hidden");
    Metronome.stop();
  });

  // ── Note labels toggle ─────────────────────────────────────────────────────

  document.getElementById("labels-toggle").addEventListener("change", (e) => {
    Keyboard.showAllLabels(e.target.checked);
  });

  // ── Shortcuts overlay ──────────────────────────────────────────────────────

  const shortcutsOverlay = document.getElementById("shortcuts-overlay");
  document.getElementById("btn-shortcuts").addEventListener("click", () => {
    shortcutsOverlay.classList.toggle("hidden");
  });
  document.getElementById("btn-shortcuts-close").addEventListener("click", () => {
    shortcutsOverlay.classList.add("hidden");
  });

  // ── Keyboard shortcuts ─────────────────────────────────────────────────────

  document.addEventListener("keydown", (e) => {
    // Don't fire when typing in an input/select
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;

    const key = e.key;

    if (key === " " || key === "Spacebar") {
      e.preventDefault();
      if (lessonStatus === "playing") {
        document.getElementById("btn-stop").click();
      } else {
        document.getElementById("btn-start").click();
      }
    } else if (key === "r" || key === "R") {
      if (!document.getElementById("btn-reference").disabled) {
        document.getElementById("btn-reference").click();
      }
    } else if (key === "m" || key === "M") {
      document.getElementById("btn-metronome").click();
    } else if (key === "d" || key === "D") {
      // Toggle drill mode
      currentMode = currentMode === "drill" ? "wait" : "drill";
      document.querySelectorAll(".seg-btn[data-mode]").forEach(b =>
        b.classList.toggle("active", b.dataset.mode === currentMode)
      );
      WS.send({ type: "set_mode", mode: currentMode });
    } else if (key === "a" || key === "A") {
      const toggle = document.getElementById("auto-speed-toggle");
      toggle.checked = !toggle.checked;
      toggle.dispatchEvent(new Event("change"));
    } else if (key === "l" || key === "L") {
      const btn = document.getElementById("btn-set-loop");
      if (!btn.disabled) btn.click();
    } else if (key === "n" || key === "N") {
      const toggle = document.getElementById("labels-toggle");
      toggle.checked = !toggle.checked;
      Keyboard.showAllLabels(toggle.checked);
    } else if (key === "1") {
      _selectHand("right");
    } else if (key === "2") {
      _selectHand("left");
    } else if (key === "3") {
      _selectHand("both");
    } else if (key === "+" || key === "=") {
      currentBpm = Math.min(200, currentBpm + 5);
      _syncBpm(currentBpm);
    } else if (key === "-") {
      currentBpm = Math.max(20, currentBpm - 5);
      _syncBpm(currentBpm);
    } else if (key === "?" || key === "/") {
      shortcutsOverlay.classList.toggle("hidden");
    } else if (key === "Escape") {
      shortcutsOverlay.classList.add("hidden");
      document.getElementById("metronome-panel").classList.add("hidden");
      document.getElementById("session-panel").classList.add("hidden");
    }
  });

  function _selectHand(hand) {
    currentHand = hand;
    document.querySelectorAll(".seg-btn[data-hand]").forEach(b =>
      b.classList.toggle("active", b.dataset.hand === hand)
    );
    WS.send({ type: "set_hand", hand });
  }

  function _syncBpm(bpm) {
    bpmSlider.value       = bpm;
    bpmDisplay.textContent = bpm;
    WS.send({ type: "set_bpm", bpm });
  }

});
