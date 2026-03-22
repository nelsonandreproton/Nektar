/**
 * metronome.js — Web Audio API metronome with beat subdivision and visual feedback.
 */
const Metronome = (() => {
  let _audioCtx   = null;
  let _bpm        = 120;
  let _beats      = 4;      // beats per bar
  let _running    = false;
  let _beat       = 0;      // current beat index (0-based)
  let _nextTime   = 0;      // next scheduled beat time (audioCtx time)
  let _schedId    = null;   // requestAnimationFrame / setTimeout handle

  // Lookahead scheduler (more accurate than setInterval alone)
  const LOOKAHEAD   = 0.1;  // seconds to schedule ahead
  const SCHEDULE_MS = 25;   // how often to call scheduler (ms)

  function _getCtx() {
    if (!_audioCtx) {
      _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    return _audioCtx;
  }

  function _playClick(time, isAccent) {
    const ctx  = _getCtx();
    const osc  = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.frequency.value = isAccent ? 1050 : 820;
    gain.gain.setValueAtTime(isAccent ? 0.45 : 0.28, time);
    gain.gain.exponentialRampToValueAtTime(0.001, time + 0.04);
    osc.start(time);
    osc.stop(time + 0.06);
  }

  function _flashBeat(beatIndex) {
    // Update visual beat lights
    const lights = document.querySelectorAll(".beat-light");
    lights.forEach((l, i) => {
      l.classList.remove("active", "accent");
      if (i === beatIndex) {
        l.classList.add(beatIndex === 0 ? "accent" : "active");
      }
    });
    // Hide lights beyond current _beats count
    lights.forEach((l, i) => {
      l.style.display = i < _beats ? "" : "none";
    });
  }

  function _scheduler() {
    if (!_running) return;
    const ctx = _getCtx();

    while (_nextTime < ctx.currentTime + LOOKAHEAD) {
      const beatIdx = _beat % _beats;
      _playClick(_nextTime, beatIdx === 0);

      // Schedule visual flash slightly before audio
      const delay = Math.max(0, (_nextTime - ctx.currentTime) * 1000);
      const b = beatIdx;
      setTimeout(() => _flashBeat(b), delay);

      _beat++;
      _nextTime += 60.0 / _bpm;
    }

    _schedId = setTimeout(_scheduler, SCHEDULE_MS);
  }

  function start() {
    if (_running) return;
    const ctx = _getCtx();
    if (ctx.state === "suspended") ctx.resume();
    _running  = true;
    _beat     = 0;
    _nextTime = ctx.currentTime + 0.05;
    _scheduler();
    _updateUI();
  }

  function stop() {
    _running = false;
    clearTimeout(_schedId);
    // Clear all beat lights
    document.querySelectorAll(".beat-light").forEach(l => {
      l.classList.remove("active", "accent");
    });
    _updateUI();
  }

  function toggle() {
    if (_running) stop(); else start();
  }

  function setBpm(bpm) {
    _bpm = Math.max(20, Math.min(280, bpm));
    document.getElementById("metro-bpm-display").textContent = _bpm;
    document.getElementById("metro-bpm-slider").value = _bpm;
    // If running, the scheduler loop picks up the new BPM automatically
  }

  function setBeats(n) {
    _beats = Math.max(2, Math.min(8, n));
    _beat  = 0;
    // Update beat lights visibility
    document.querySelectorAll(".beat-light").forEach((l, i) => {
      l.style.display = i < _beats ? "" : "none";
      l.classList.remove("active", "accent");
    });
    // Highlight active beats button
    document.querySelectorAll("[data-beats]").forEach(b => {
      b.classList.toggle("active", parseInt(b.dataset.beats) === _beats);
    });
  }

  function _updateUI() {
    const btn = document.getElementById("btn-metro-toggle");
    const headerBtn = document.getElementById("btn-metronome");
    if (btn) {
      btn.textContent = _running ? "■ Stop" : "▶ Start";
      btn.classList.toggle("running", _running);
    }
    if (headerBtn) headerBtn.classList.toggle("active", _running);
  }

  // Wire up DOM after load
  document.addEventListener("DOMContentLoaded", () => {
    const bpmSlider = document.getElementById("metro-bpm-slider");
    if (bpmSlider) {
      bpmSlider.addEventListener("input", () => setBpm(parseInt(bpmSlider.value)));
    }

    const toggleBtn = document.getElementById("btn-metro-toggle");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", toggle);
    }

    // Beats selector
    document.querySelectorAll("[data-beats]").forEach(btn => {
      btn.addEventListener("click", () => setBeats(parseInt(btn.dataset.beats)));
    });

    // Set default beat visibility
    setBeats(4);
  });

  return { start, stop, toggle, setBpm, setBeats, isRunning: () => _running };
})();
