/**
 * app.js — main controller.
 * Wires WebSocket events → Keyboard + LessonUI, and UI controls → WebSocket.
 */
document.addEventListener("DOMContentLoaded", () => {

  // ── State ──────────────────────────────────────────────────────────────────
  let currentHand = "right";
  let currentBpm  = 60;
  let lessonStatus = "idle";  // idle | playing | completed

  // ── WebSocket lifecycle ────────────────────────────────────────────────────

  window.addEventListener("ws:open", () => {
    WS.send({ type: "get_devices" });
    WS.send({ type: "get_lessons" });
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
      // Auto-select Nektar
      if (name.toLowerCase().includes("nektar")) opt.selected = true;
      sel.appendChild(opt);
    }
    // Auto-connect if Nektar found
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
    document.getElementById("btn-start").disabled = false;
    document.getElementById("btn-reference").disabled = false;
  });

  // ── MIDI input events ──────────────────────────────────────────────────────

  window.addEventListener("ws:note_on", (e) => {
    const { note, result } = e.detail;
    Keyboard.setState(note, "pressed", true);
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

  // ── Lesson state updates ───────────────────────────────────────────────────

  window.addEventListener("ws:lesson_state", (e) => {
    applyState(e.detail.state);
  });

  window.addEventListener("ws:lesson_complete", (e) => {
    const score = e.detail.score;
    lessonStatus = "completed";

    Keyboard.clearAll();
    LessonUI.updateHint(null);

    const pct = score.total > 0 ? Math.round((score.correct / score.total) * 100) : 0;
    const emoji = pct === 100 ? "🎉" : pct >= 80 ? "🎹" : "👍";
    document.getElementById("hint-label").textContent =
      `${emoji} Complete! Accuracy: ${pct}%  (${score.correct}/${score.total} correct)`;

    document.getElementById("btn-stop").disabled = true;
    document.getElementById("btn-start").disabled = false;
  });

  function applyState(state) {
    if (!state) return;
    lessonStatus = state.status;

    // Update hint / expected keys
    const expected = state.current_expected || [];
    Keyboard.setExpected(expected);
    LessonUI.updateHint(expected.length > 0 ? expected : null);
    LessonUI.updateScore(state);

    // Sync BPM slider
    if (state.bpm && state.bpm !== currentBpm) {
      currentBpm = state.bpm;
      document.getElementById("bpm-slider").value = currentBpm;
      document.getElementById("bpm-display").textContent = currentBpm;
    }

    // Sync hand buttons
    if (state.hand && state.hand !== currentHand) {
      currentHand = state.hand;
      document.querySelectorAll(".seg-btn[data-hand]").forEach(b => {
        b.classList.toggle("active", b.dataset.hand === currentHand);
      });
    }

    // Button visibility
    const playing = state.status === "playing";
    document.getElementById("btn-stop").disabled = !playing;
    document.getElementById("btn-start").disabled = playing;
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
    WS.send({ type: "start_lesson", lesson_id: id, hand: currentHand });
  });

  document.getElementById("btn-stop").addEventListener("click", () => {
    WS.send({ type: "stop_lesson" });
    WS.send({ type: "stop_reference" });
    Keyboard.clearAll();
    LessonUI.updateHint(null);
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

  // BPM slider
  const bpmSlider = document.getElementById("bpm-slider");
  const bpmDisplay = document.getElementById("bpm-display");
  bpmSlider.addEventListener("input", () => {
    currentBpm = parseInt(bpmSlider.value);
    bpmDisplay.textContent = currentBpm;
    WS.send({ type: "set_bpm", bpm: currentBpm });
  });

  // ── MIDI file import ───────────────────────────────────────────────────────

  document.getElementById("midi-file-input").addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const bytes = new Uint8Array(reader.result);
      let binary = "";
      for (const byte of bytes) binary += String.fromCharCode(byte);
      WS.send({
        type: "load_midi",
        filename: file.name,
        content: btoa(binary),
      });
    };
    reader.readAsArrayBuffer(file);
    // Reset so same file can be re-imported
    e.target.value = "";
  });

  // ── Error notifications ────────────────────────────────────────────────────

  window.addEventListener("ws:error", (e) => {
    console.warn("[Server error]", e.detail.message);
    // Simple non-intrusive notification via hint label
    const label = document.getElementById("hint-label");
    const prev = label.textContent;
    label.style.color = "var(--red)";
    label.textContent = "⚠ " + e.detail.message;
    setTimeout(() => {
      label.style.color = "";
      label.textContent = prev;
    }, 3000);
  });

});
