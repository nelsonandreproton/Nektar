/**
 * Virtual 61-key piano keyboard (MIDI 36–96, C2–C7).
 * Renders CSS div keys; exposes setState(note, state) for colour changes.
 */
const Keyboard = (() => {
  const START_MIDI = 36;   // C2
  const END_MIDI   = 96;   // C7
  const TOTAL_KEYS = END_MIDI - START_MIDI + 1; // 61

  // Semitone → white-key index within octave (-1 = black key)
  const WHITE_KEY_IDX = [0, -1, 1, -1, 2, 3, -1, 4, -1, 5, -1, 6];
  // Semitone → black key fractional offset within octave (in white-key units)
  const BLACK_KEY_OFF = { 1: 0.67, 3: 1.67, 6: 3.67, 8: 4.67, 10: 5.67 };

  const NOTE_NAMES   = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"];
  const WHITE_TOTAL  = 36; // 5 × 7 + 1

  let keyEls = {}; // midi → div element
  let keyStates = {}; // midi → Set of active state strings

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

    const cw = container.clientWidth || window.innerWidth - 8;
    const kh = container.clientHeight || 164;
    const ww = cw / WHITE_TOTAL;          // white key width
    const bw = ww * 0.62;                 // black key width
    const wh = kh;
    const bh = Math.round(kh * 0.62);

    // Render white keys first, then black (higher z-index)
    for (let midi = START_MIDI; midi <= END_MIDI; midi++) {
      if (isBlack(midi)) continue;
      const wi   = getWhiteIndex(midi);
      const el   = document.createElement("div");
      el.className = "key-white";
      el.dataset.midi = midi;
      el.style.left   = `${wi * ww}px`;
      el.style.width  = `${ww - 1}px`;
      el.style.height = `${wh}px`;

      // Label C notes
      const sem = (midi - START_MIDI) % 12;
      if (sem === 0) {
        const octave = Math.floor(midi / 12) - 1;
        const lbl = document.createElement("span");
        lbl.className = "key-label";
        lbl.textContent = `C${octave}`;
        el.appendChild(lbl);
      }

      keyEls[midi] = el;
      keyStates[midi] = new Set();
      container.appendChild(el);
    }

    for (let midi = START_MIDI; midi <= END_MIDI; midi++) {
      if (!isBlack(midi)) continue;
      const octave   = Math.floor((midi - START_MIDI) / 12);
      const semitone = (midi - START_MIDI) % 12;
      const offset   = BLACK_KEY_OFF[semitone];

      const el   = document.createElement("div");
      el.className = "key-black";
      el.dataset.midi = midi;
      el.style.left   = `${(octave * 7 + offset) * ww - bw / 2}px`;
      el.style.width  = `${bw}px`;
      el.style.height = `${bh}px`;

      keyEls[midi] = el;
      keyStates[midi] = new Set();
      container.appendChild(el);
    }
  }

  // Rebuild on window resize
  window.addEventListener("resize", () => {
    build();
  });

  /**
   * Apply a named state to a key.
   * state: 'pressed' | 'expected' | 'correct' | 'wrong' | 'playback'
   * on: true to add, false to remove
   */
  function setState(midi, state, on) {
    if (!keyEls[midi]) return;
    const el = keyEls[midi];
    const states = keyStates[midi];

    if (on) {
      states.add(state);
    } else {
      states.delete(state);
    }

    // Priority order: correct > wrong > pressed > playback > expected
    el.classList.remove("key-expected", "key-correct", "key-wrong", "key-pressed", "key-playback");
    if (states.has("correct"))  el.classList.add("key-correct");
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
  }

  function setExpected(midiList) {
    // Remove previous expected states
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

  function noteName(midi) {
    const name = NOTE_NAMES[midi % 12];
    const octave = Math.floor(midi / 12) - 1;
    return `${name}${octave}`;
  }

  // Initialize
  document.addEventListener("DOMContentLoaded", build);

  return { setState, clearAll, setExpected, flashCorrect, flashWrong, noteName };
})();
