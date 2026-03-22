/**
 * staff.js — VexFlow staff notation display.
 * Shows current expected notes on a treble (or bass) clef.
 */
const StaffView = (() => {
  let _renderer  = null;
  let _context   = null;
  let _ready     = false;
  let _visible   = true;

  const WIDTH  = 300;
  const HEIGHT = 130;

  // VexFlow note name mapping from MIDI semitone
  const VEX_NAMES = ["c","c","d","d","e","f","f","g","g","a","a","b"];
  const VEX_ACCS  = [null,"#",null,"#",null,null,"#",null,"#",null,"#",null];

  function init() {
    if (!window.Vex) {
      // VexFlow not loaded — gracefully hide the panel
      const panel = document.getElementById("staff-panel");
      if (panel) panel.classList.add("hidden");
      return;
    }

    const el = document.getElementById("staff-canvas");
    if (!el) return;

    try {
      const { Renderer } = Vex.Flow;
      _renderer = new Renderer(el, Renderer.Backends.SVG);
      _renderer.resize(WIDTH, HEIGHT);
      _context  = _renderer.getContext();
      _context.setFont("Arial", 10);
      _ready    = true;
      render([]);
    } catch (err) {
      console.warn("[StaffView] VexFlow init failed:", err);
      const panel = document.getElementById("staff-panel");
      if (panel) panel.classList.add("hidden");
    }
  }

  function midiToVex(midi) {
    const semitone = midi % 12;
    const octave   = Math.floor(midi / 12) - 1;
    return {
      key: `${VEX_NAMES[semitone]}/${octave}`,
      acc: VEX_ACCS[semitone],
    };
  }

  // Pick clef based on note range
  function chooseClef(midiNotes) {
    if (!midiNotes || midiNotes.length === 0) return "treble";
    const avg = midiNotes.reduce((a, b) => a + b, 0) / midiNotes.length;
    return avg < 57 ? "bass" : "treble";
  }

  function render(midiNotes) {
    if (!_ready || !_visible) return;

    const { Stave, StaveNote, Voice, Formatter, Accidental } = Vex.Flow;

    // Clear by resizing (clears SVG)
    _renderer.resize(WIDTH, HEIGHT);
    _context = _renderer.getContext();
    _context.setFont("Arial", 10);

    const clef  = chooseClef(midiNotes);
    const stave = new Stave(10, 15, WIDTH - 20);
    stave.addClef(clef);
    stave.setContext(_context).draw();

    if (!midiNotes || midiNotes.length === 0) return;

    try {
      const vexData = midiNotes.map(midiToVex);
      const keys    = vexData.map(v => v.key);

      const staveNote = new StaveNote({
        keys,
        duration: "w",
        clef,
      });

      vexData.forEach((v, i) => {
        if (v.acc) {
          staveNote.addModifier(new Accidental(v.acc), i);
        }
      });

      const voice = new Voice({ num_beats: 4, beat_value: 4 });
      voice.setStrict(false);
      voice.addTickables([staveNote]);

      new Formatter()
        .joinVoices([voice])
        .format([voice], WIDTH - 60);

      voice.draw(_context, stave);
    } catch (err) {
      // Silently ignore rendering errors (e.g., notes out of staff range)
      console.debug("[StaffView] render error:", err.message);
    }
  }

  function setVisible(show) {
    _visible = show;
    const panel = document.getElementById("staff-panel");
    if (panel) panel.classList.toggle("hidden", !show);
    if (show) render(_lastNotes);
  }

  let _lastNotes = [];
  function update(midiNotes) {
    _lastNotes = midiNotes || [];
    render(_lastNotes);
  }

  // Init after DOM ready
  document.addEventListener("DOMContentLoaded", () => {
    // Small delay to allow VexFlow CDN script to finish executing
    setTimeout(init, 100);

    const toggle = document.getElementById("staff-toggle");
    if (toggle) {
      toggle.addEventListener("change", () => setVisible(toggle.checked));
    }
  });

  return { update, setVisible };
})();
