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
  let isAssessing     = false;    // true when current lesson was started as an attempt
  let currentMinBpm   = null;     // min_bpm for active course step (if any)

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
      sel.appendChild(opt);
    }
    // Auto-select: single device, or first non-virtual device
    if (inputs.length === 1) {
      sel.options[1].selected = true;
    } else if (inputs.length > 1) {
      const preferred = inputs.find(n => !n.toLowerCase().includes("midiin2") && !n.toLowerCase().includes("virtual") && !n.toLowerCase().includes("microsoft"));
      const idx = preferred ? inputs.indexOf(preferred) + 1 : 1;
      sel.options[idx].selected = true;
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
    _enableStartButtons(true);
    document.getElementById("btn-reference").disabled = false;
  });

  // ── Course events ───────────────────────────────────────────────────────────

  CourseUI.init((lessonId, hand, minBpm) => {
    // User clicked a course step — select that lesson and set hand
    const allLessons = LessonUI.getAllLessons();
    const lesson     = allLessons.find(l => l.id === lessonId);
    if (lesson) LessonUI.selectLesson(lesson);

    currentHand = hand;
    _syncHandButtons(hand);
    _lockHandButtons(true);  // hand is fixed by curriculum in course mode
    WS.send({ type: "set_hand", hand });

    // Show min-BPM requirement if applicable
    currentMinBpm = minBpm || null;
    _updateMinBpmDisplay(currentMinBpm);

    _enableStartButtons(true);
    document.getElementById("btn-reference").disabled = false;
    document.getElementById("coaching-panel").classList.add("hidden");
    document.getElementById("course-feedback").classList.add("hidden");
  });

  window.addEventListener("ws:course_state", (e) => {
    CourseUI.render(e.detail.course);
    _syncCourseWelcome(e.detail.course);
  });

  window.addEventListener("ws:course_attempt", (e) => {
    const { feedback, tips, course } = e.detail;
    CourseUI.showAttemptFeedback(feedback);
    CourseUI.render(course);

    // Show coaching tips if the attempt failed
    if (tips && tips.length > 0) {
      _showCoachingTips(tips);
    }

    // Auto-select next lesson when newly mastered
    if (courseMode && feedback.newly_mastered) {
      const nextStep = course.curriculum[course.current_index];
      if (nextStep) {
        setTimeout(() => _selectCourseStep(nextStep, course), 800);
      }
    }
  });

  function _selectCourseStep(step, courseState) {
    const allLessons = LessonUI.getAllLessons();
    const lesson = allLessons.find(l => l.id === step.lesson_id);
    if (lesson) LessonUI.selectLesson(lesson);

    currentHand   = step.hand;
    currentMinBpm = step.min_bpm || null;
    _syncHandButtons(step.hand);
    _lockHandButtons(true);
    WS.send({ type: "set_hand", hand: step.hand });
    _updateMinBpmDisplay(currentMinBpm);
    _enableStartButtons(true);
    document.getElementById("btn-reference").disabled = false;
  }

  function _syncCourseWelcome(courseState) {
    if (!courseState) return;
    if (!courseState.diagnostic_complete && courseMode) {
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
    // Show practice/assess buttons, hide legacy Start
    _setCourseButtonsVisible(true);
    WS.send({ type: "get_course" });
  });

  // Non-course category tabs
  document.querySelectorAll(".cat-btn:not(#btn-course-tab)").forEach(btn => {
    btn.addEventListener("click", () => {
      courseMode = false;
      document.getElementById("lesson-list").classList.remove("hidden");
      document.getElementById("course-panel").classList.add("hidden");
      _setCourseButtonsVisible(false);
      _lockHandButtons(false);
      _updateMinBpmDisplay(null);
    });
  });

  function _setCourseButtonsVisible(isCourse) {
    document.getElementById("btn-start").classList.toggle("hidden", isCourse);
    document.getElementById("btn-practice").classList.toggle("hidden", !isCourse);
    document.getElementById("btn-assess").classList.toggle("hidden", !isCourse);
  }

  // ── Course: export / import / reset ───────────────────────────────────────

  document.getElementById("btn-reset-course").addEventListener("click", () => {
    if (confirm("Tens a certeza que queres apagar todo o progresso do curso?")) {
      WS.send({ type: "reset_course" });
    }
  });

  document.getElementById("btn-export-course").addEventListener("click", () => {
    WS.send({ type: "export_course" });
  });

  window.addEventListener("ws:course_export", (e) => {
    const blob = new Blob([JSON.stringify(e.detail.content, null, 2)],
                          { type: "application/json" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = "nektar_progress.json";
    a.click();
    URL.revokeObjectURL(url);
  });

  document.getElementById("course-import-input").addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const content = JSON.parse(reader.result);
        WS.send({ type: "import_course", content });
      } catch {
        alert("Ficheiro JSON inválido ou corrompido.");
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  });

  // ── Coaching tips panel ────────────────────────────────────────────────────

  document.getElementById("btn-coaching-close").addEventListener("click", () => {
    document.getElementById("coaching-panel").classList.add("hidden");
  });

  function _showCoachingTips(tips) {
    const panel = document.getElementById("coaching-panel");
    const list  = document.getElementById("coaching-tips");
    list.innerHTML = "";
    for (const tip of tips) {
      const li = document.createElement("li");
      li.textContent = tip;
      list.appendChild(li);
    }
    panel.classList.remove("hidden");
  }

  // ── Min BPM display ────────────────────────────────────────────────────────

  function _updateMinBpmDisplay(minBpm) {
    const row   = document.getElementById("min-bpm-row");
    const chip  = document.getElementById("min-bpm-display");
    if (minBpm) {
      chip.textContent = `≥ ${minBpm} BPM`;
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  }

  // ── MIDI input events ──────────────────────────────────────────────────────

  window.addEventListener("ws:note_on", (e) => {
    const { note, result, velocity, expected } = e.detail;
    Keyboard.setState(note, "pressed", true);
    Keyboard.setVelocity(note, velocity || 80);
    LessonUI.markChipPressed(note, true);

    if (result === "correct") {
      Keyboard.flashCorrect(note);
      LessonUI.flashResult("correct");
    } else if (result === "wrong") {
      Keyboard.flashWrong(note);
      LessonUI.flashResult("wrong");

      // Show what was expected
      if (expected && expected.length > 0) {
        _flashWrongNoteHint(note, expected);
      }
    }
  });

  window.addEventListener("ws:note_off", (e) => {
    const { note } = e.detail;
    Keyboard.setState(note, "pressed", false);
    LessonUI.markChipPressed(note, false);
  });

  function _flashWrongNoteHint(pressedNote, expectedNotes) {
    const label = document.getElementById("hint-label");
    const pressedName   = _midiNoteName(pressedNote);
    const expectedNames = expectedNotes.map(_midiNoteName).join(", ");
    const prev = label.textContent;
    label.style.color   = "var(--red)";
    label.textContent   = `Premiste ${pressedName} — era ${expectedNames}`;
    clearTimeout(label._wrongTimer);
    label._wrongTimer = setTimeout(() => {
      label.style.color = "";
      label.textContent = prev;
    }, 2000);
  }

  const _NOTE_NAMES_PT = ["Dó","Dó#","Ré","Ré#","Mi","Fá","Fá#","Sol","Sol#","Lá","Lá#","Si"];
  function _midiNoteName(midi) {
    const oct = Math.floor(midi / 12) - 1;
    return _NOTE_NAMES_PT[midi % 12] + oct;
  }

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
    isAssessing  = false;

    Keyboard.clearAll();
    LessonUI.updateHint(null);
    LessonUI.updateNextNotes([]);
    StaffView.update([]);

    const stepsAttempted = score.correct + (score.wrong_steps || 0);
    const pct   = stepsAttempted > 0 ? Math.round((score.correct / stepsAttempted) * 100) : 0;
    const emoji = pct === 100 ? "🎉" : pct >= 80 ? "🎹" : "👍";
    document.getElementById("hint-label").textContent =
      `${emoji} Completo! Precisão: ${pct}%  (${score.correct}/${score.total} correctas)`;

    document.getElementById("btn-stop").disabled = true;
    _enableStartButtons(true);
    document.getElementById("btn-assess").classList.remove("assessing");

    if (pct >= 70) LessonUI.markLessonComplete(LessonUI.getActiveLessonId());
    Session.recordResult(score.correct, score.wrong);
  });

  function applyState(state) {
    if (!state) return;
    lessonStatus = state.status;

    const expected   = state.current_expected  || [];
    const fingering  = state.current_fingering || {};
    const nextNotes  = state.next_notes        || [];

    Keyboard.setExpected(expected);
    Keyboard.setFingering(fingering);
    LessonUI.updateHint(expected.length > 0 ? expected : null, fingering);
    LessonUI.updateNextNotes(nextNotes);
    LessonUI.updateScore(state);
    StaffView.update(expected);

    if (state.bpm !== undefined && state.bpm !== currentBpm) {
      currentBpm = state.bpm;
      document.getElementById("bpm-slider").value        = Math.round(currentBpm);
      document.getElementById("bpm-display").textContent = Math.round(currentBpm);
    }

    if (state.hand && state.hand !== currentHand) {
      currentHand = state.hand;
      _syncHandButtons(currentHand);
    }

    if (state.mode && state.mode !== currentMode) {
      currentMode = state.mode;
      document.querySelectorAll(".seg-btn[data-mode]").forEach(b =>
        b.classList.toggle("active", b.dataset.mode === currentMode)
      );
    }

    const autoToggle = document.getElementById("auto-speed-toggle");
    if (autoToggle && autoToggle.checked !== state.auto_speed) {
      autoToggle.checked = state.auto_speed;
    }

    const playing = state.status === "playing";
    document.getElementById("btn-stop").disabled     = !playing;
    document.getElementById("btn-set-loop").disabled = !playing;
    _enableStartButtons(!playing);
  }

  // ── Playback events ────────────────────────────────────────────────────────

  window.addEventListener("ws:playback_note_on", (e) => {
    Keyboard.setState(e.detail.note, "playback", true);
  });
  window.addEventListener("ws:playback_note_off", (e) => {
    Keyboard.setState(e.detail.note, "playback", false);
  });

  // ── Controls ───────────────────────────────────────────────────────────────

  // Course mode: Praticar button
  document.getElementById("btn-practice").addEventListener("click", () => {
    _startLesson(false);
  });

  // Course mode: Tentar button (counts toward mastery)
  document.getElementById("btn-assess").addEventListener("click", () => {
    _startLesson(true);
  });

  // Free-play Start button
  document.getElementById("btn-start").addEventListener("click", () => {
    _startLesson(false);
  });

  function _startLesson(assess) {
    const id = LessonUI.getActiveLessonId();
    if (!id) return;
    isAssessing = assess;
    Keyboard.clearAll();
    LessonUI.resetScore();
    loopPending   = false;
    loopStartStep = null;
    document.getElementById("course-feedback").classList.add("hidden");
    document.getElementById("coaching-panel").classList.add("hidden");
    // Mark btn-assess as "assessing" (orange) while lesson runs
    document.getElementById("btn-assess").classList.toggle("assessing", assess);
    WS.send({ type: "start_lesson", lesson_id: id, hand: currentHand, assess });
    CourseUI.setActiveLessonId(id, currentHand);
    Session.startTimer();
    Session.recordLessonPlayed(id);
  }

  document.getElementById("btn-stop").addEventListener("click", () => {
    isAssessing = false;
    document.getElementById("btn-assess").classList.remove("assessing");
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
    if (!btn || btn.disabled) return;
    currentHand = btn.dataset.hand;
    _syncHandButtons(currentHand);
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
    const stepText = document.getElementById("score-step").textContent;
    const match    = stepText.match(/^(\d+)\s*\/\s*(\d+)/);
    if (!match) return;
    const currentStep = parseInt(match[1]);

    if (!loopPending) {
      loopStartStep = currentStep;
      loopPending   = true;
      document.getElementById("btn-set-loop").textContent = "[ End ]";
    } else {
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
      WS.send({ type: "load_midi", filename: file.name, content: btoa(binary) });
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
    setTimeout(() => { label.style.color = ""; label.textContent = prev; }, 3000);
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

  // ── Initialise button visibility (non-course mode is the default) ──────────

  _setCourseButtonsVisible(false);

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
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;

    const key = e.key;

    if (key === " " || key === "Spacebar") {
      e.preventDefault();
      if (lessonStatus === "playing") {
        document.getElementById("btn-stop").click();
      } else if (courseMode) {
        // Space in course mode → Praticar
        document.getElementById("btn-practice").click();
      } else {
        document.getElementById("btn-start").click();
      }
    } else if (key === "Enter") {
      // Enter in course mode → Tentar (assess)
      if (courseMode && lessonStatus !== "playing") {
        document.getElementById("btn-assess").click();
      }
    } else if (key === "r" || key === "R") {
      if (!document.getElementById("btn-reference").disabled)
        document.getElementById("btn-reference").click();
    } else if (key === "m" || key === "M") {
      document.getElementById("btn-metronome").click();
    } else if (key === "d" || key === "D") {
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
      document.getElementById("coaching-panel").classList.add("hidden");
    }
  });

  // ── Helpers ────────────────────────────────────────────────────────────────

  function _enableStartButtons(enabled) {
    if (courseMode) {
      document.getElementById("btn-practice").disabled = !enabled;
      document.getElementById("btn-assess").disabled   = !enabled;
    } else {
      document.getElementById("btn-start").disabled = !enabled;
    }
  }

  function _lockHandButtons(locked) {
    document.querySelectorAll(".seg-btn[data-hand]").forEach(b => {
      b.disabled = locked;
    });
  }

  function _syncHandButtons(hand) {
    document.querySelectorAll(".seg-btn[data-hand]").forEach(b =>
      b.classList.toggle("active", b.dataset.hand === hand)
    );
  }

  function _selectHand(hand) {
    currentHand = hand;
    _syncHandButtons(hand);
    WS.send({ type: "set_hand", hand });
  }

  function _syncBpm(bpm) {
    bpmSlider.value        = bpm;
    bpmDisplay.textContent = bpm;
    WS.send({ type: "set_bpm", bpm });
  }

});
