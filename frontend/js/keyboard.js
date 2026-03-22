/**
 * Virtual 61-key piano keyboard (MIDI 36–96, C2–C7).
 * Renders CSS div keys; exposes setState/setExpected/setVelocity/setFingering.
 */
const Keyboard = (() => {
  const START_MIDI = 36;   // C2
  const END_MIDI   = 96;   // C7
  const TOTAL_KEYS = END_MIDI - START_MIDI + 1; // 61

  // Semitone → white-key index within octave (-1 = black key)
  const WHITE_KEY_IDX = [0, -1, 1, -1, 2, 3, -1, 4, -1, 5, -1, 6];
  // Semitone → black key fractional offset within octave (in white-key units)
  const BLACK_KEY_OFF = { 1: 0.67, 3: 1.67, 6: 3.67, 8: 4.67, 10: 5.67 };

  const NOTE_NAMES  = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"];
  const WHITE_TOTAL = 36; // 5 × 7 + 1

  let keyEls     = {}; // midi → div element
  let keyStates  = {}; // midi → Set of active state strings
  let velBarEls  = {}; // midi → velocity bar div
  let fingerEls  = {}; // midi → finger label span

  // White key pixel width (set during build)
  let _ww = 0;

  function isBlack(midi) {
    return WHITE_KEY_IDX[(midi - START_MIDI) % 12] === -1;
  }

  function getWhiteIndex(midi) {
    const octave   = Math.floor((midi - START_MIDI) / 12);
    const semitone = (midi - START_MIDI) % 12;
    const wi       = WHITE_KEY_IDX[semitone];
    return wi === -1 ? -1 : octave * 7 + wi;
  }

  function build() {
    const container = document.getElementById("keyboard");
    container.innerHTML = "";
    // Clear velocity bar row
    const velRow = document.getElementById("velocity-bar-row");
    if (velRow) velRow.innerHTML = "";

    keyEls    = {};
    keyStates = {};
    velBarEls = {};
    fingerEls = {};

    const cw = container.clientWidth || window.innerWidth - 8;
    const kh = container.clientHeight || 156;
    const ww = cw / WHITE_TOTAL;      // white key width
    const bw = ww * 0.62;             // black key width
    const wh = kh;
    const bh = Math.round(kh * 0.62);
    _ww = ww;

    // Render white keys first
    for (let midi = START_MIDI; midi <= END_MIDI; midi++) {
      if (isBlack(midi)) continue;
      const wi  = getWhiteIndex(midi);
      const el  = document.createElement("div");
      el.className = "key-white";
      el.dataset.midi = midi;
      el.style.left   = `${wi * ww}px`;
      el.style.width  = `${ww - 1}px`;
      el.style.height = `${wh}px`;

      // Finger number label (hidden until set)
      const fingerLbl = document.createElement("span");
      fingerLbl.className = "key-finger";
      fingerLbl.style.display = "none";
      el.appendChild(fingerLbl);
      fingerEls[midi] = fingerLbl;

      // C note label (always visible)
      const sem = (midi - START_MIDI) % 12;
      if (sem === 0) {
        const octave = Math.floor(midi / 12) - 1;
        const lbl = document.createElement("span");
        lbl.className = "key-label";
        lbl.textContent = `C${octave}`;
        el.appendChild(lbl);
      }

      // All-notes label (shown when show-all-labels class is on #keyboard)
      const allLbl = document.createElement("span");
      allLbl.className = "key-label-all";
      allLbl.textContent = NOTE_NAMES[(midi - START_MIDI) % 12];
      el.appendChild(allLbl);

      keyEls[midi]    = el;
      keyStates[midi] = new Set();
      container.appendChild(el);

      // Velocity bar for this key
      if (velRow) {
        const vb = document.createElement("div");
        vb.className = "vel-bar";
        vb.style.left  = `${wi * ww}px`;
        vb.style.width = `${ww - 1}px`;
        vb.style.opacity = "0";
        velRow.appendChild(vb);
        velBarEls[midi] = vb;
      }
    }

    // Render black keys on top
    for (let midi = START_MIDI; midi <= END_MIDI; midi++) {
      if (!isBlack(midi)) continue;
      const octave   = Math.floor((midi - START_MIDI) / 12);
      const semitone = (midi - START_MIDI) % 12;
      const offset   = BLACK_KEY_OFF[semitone];

      const el = document.createElement("div");
      el.className = "key-black";
      el.dataset.midi = midi;
      el.style.left   = `${(octave * 7 + offset) * ww - bw / 2}px`;
      el.style.width  = `${bw}px`;
      el.style.height = `${bh}px`;

      // Finger number label
      const fingerLbl = document.createElement("span");
      fingerLbl.className = "key-finger";
      fingerLbl.style.display = "none";
      el.appendChild(fingerLbl);
      fingerEls[midi] = fingerLbl;

      // All-notes label
      const allLbl = document.createElement("span");
      allLbl.className = "key-label-all";
      allLbl.textContent = NOTE_NAMES[(midi - START_MIDI) % 12];
      el.appendChild(allLbl);

      keyEls[midi]    = el;
      keyStates[midi] = new Set();
      container.appendChild(el);
    }
  }

  // Rebuild on window resize (debounced)
  let _resizeTimer = null;
  window.addEventListener("resize", () => {
    clearTimeout(_resizeTimer);
    _resizeTimer = setTimeout(build, 150);
  });

  /**
   * Apply a named state to a key.
   * state: 'pressed' | 'expected' | 'correct' | 'wrong' | 'playback'
   * on: true to add, false to remove
   */
  function setState(midi, state, on) {
    if (midi < 0 || midi > 127) return;
    if (!keyEls[midi]) return;
    const el     = keyEls[midi];
    const states = keyStates[midi];

    if (on) { states.add(state); }
    else     { states.delete(state); }

    // Priority: correct > wrong > pressed > playback > expected
    el.classList.remove("key-expected", "key-correct", "key-wrong", "key-pressed", "key-playback");
    if      (states.has("correct"))  el.classList.add("key-correct");
    else if (states.has("wrong"))    el.classList.add("key-wrong");
    else if (states.has("pressed"))  el.classList.add("key-pressed");
    else if (states.has("playback")) el.classList.add("key-playback");
    else if (states.has("expected")) el.classList.add("key-expected");
  }

  function clearAll() {
    for (const midi of Object.keys(keyEls)) {
      keyStates[midi] = new Set();
      const el = keyEls[midi];
      el.classList.remove("key-expected", "key-correct", "key-wrong", "key-pressed", "key-playback");
    }
    clearAllFingering();
  }

  function setExpected(midiList) {
    for (const midi of Object.keys(keyEls)) {
      setState(parseInt(midi), "expected", false);
    }
    for (const midi of (midiList || [])) {
      setState(midi, "expected", true);
    }
  }

  function flashCorrect(midi) {
    setState(midi, "correct", true);
    setTimeout(() => setState(midi, "correct", false), 500);
  }

  function flashWrong(midi) {
    setState(midi, "wrong", true);
    setTimeout(() => setState(midi, "wrong", false), 400);
  }

  // ── Velocity display ────────────────────────────────────────────────────

  let _velTimers = {};

  function setVelocity(midi, velocity) {
    const vb = velBarEls[midi];
    if (!vb) return;
    // velocity 0-127 → opacity 0.3-1.0, width is already set per key
    const opacity = 0.3 + (velocity / 127) * 0.7;
    vb.style.opacity = opacity.toFixed(2);
    // Color: soft blue at low velocity, bright blue at high
    const r = Math.round(79  + (velocity / 127) * 50);
    const g = Math.round(195 - (velocity / 127) * 60);
    const b = Math.round(247);
    vb.style.background = `rgb(${r},${g},${b})`;

    clearTimeout(_velTimers[midi]);
    _velTimers[midi] = setTimeout(() => {
      if (vb) vb.style.opacity = "0";
    }, 800);
  }

  // ── Fingering display ───────────────────────────────────────────────────

  function setFingering(fingeringMap) {
    // fingeringMap: { "60": 1, "62": 2, ... }
    clearAllFingering();
    for (const [midiStr, finger] of Object.entries(fingeringMap || {})) {
      const el = fingerEls[parseInt(midiStr)];
      if (el) {
        el.textContent = finger;
        el.style.display = "block";
      }
    }
  }

  function clearAllFingering() {
    for (const el of Object.values(fingerEls)) {
      if (el) el.style.display = "none";
    }
  }

  // ── Note name label toggle ──────────────────────────────────────────────

  function showAllLabels(show) {
    const container = document.getElementById("keyboard");
    if (container) {
      container.classList.toggle("show-all-labels", show);
    }
  }

  // ── Utility ─────────────────────────────────────────────────────────────

  function noteName(midi) {
    const name   = NOTE_NAMES[midi % 12];
    const octave = Math.floor(midi / 12) - 1;
    return `${name}${octave}`;
  }

  // Initialize
  document.addEventListener("DOMContentLoaded", build);

  return {
    setState,
    clearAll,
    setExpected,
    flashCorrect,
    flashWrong,
    setVelocity,
    setFingering,
    clearAllFingering,
    showAllLabels,
    noteName,
  };
})();
