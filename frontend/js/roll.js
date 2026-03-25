/**
 * Roll — Synthesia-style falling notes piano roll.
 *
 * Two modes:
 *   'visual' — notes fall for timing guidance; engine handles scoring (wait/drill)
 *   'timed'  — notes must be hit within TIMING_WINDOW_MS of the beat;
 *               Roll owns scoring and calls onComplete({correct, wrong_steps, total})
 *               when all note windows have closed.
 *
 * Configurable constants (top of file):
 *   TIMING_WINDOW_MS  — ± ms around a beat that counts as a hit  (default 300)
 *   COUNTDOWN_BEATS   — beats to count down before roll starts    (default 4)
 */
const Roll = (() => {

  // ── Configurable ────────────────────────────────────────────────────────────
  const TIMING_WINDOW_MS = 300;
  const COUNTDOWN_BEATS  = 4;

  // ── Keyboard geometry (mirrors keyboard.js) ──────────────────────────────────
  const START_MIDI    = 36;
  const WHITE_TOTAL   = 36;
  const WHITE_KEY_IDX = [0, -1, 1, -1, 2, 3, -1, 4, -1, 5, -1, 6];
  const BLACK_KEY_OFF = { 1: 0.67, 3: 1.67, 6: 3.67, 8: 4.67, 10: 5.67 };

  // ── Layout ──────────────────────────────────────────────────────────────────
  const HIT_Y_FRAC  = 0.88;
  const PX_PER_BEAT = 90;
  const NOTE_RADIUS = 3;
  const FLASH_MS    = 400;   // visual-mode flash duration

  // ── State ────────────────────────────────────────────────────────────────────
  let _canvas         = null;
  let _ctx            = null;
  let _steps          = [];       // [{beat, duration, notes, hand, state, pressed}]
  let _bpm            = 60;
  let _startMs        = 0;        // wall-clock ms when beat-0 begins (after countdown)
  let _cdStartMs      = 0;        // wall-clock ms when countdown began
  let _rafId          = null;
  let _playing        = false;
  let _mode           = 'visual'; // 'visual' | 'timed'
  let _onComplete     = null;
  let _onStepChange   = null;     // timed: called with notes[] when active step changes
  let _flashMap       = new Map();  // visual mode: midi → {endMs, correct}
  let _done           = false;      // timed: completion already fired
  let _lastActiveStep = -1;         // timed: index of last notified step
  let _lastTickBeat   = -1;         // countdown: last beat index that triggered a tick
  let _audioCtx       = null;

  // ── Key geometry helpers ─────────────────────────────────────────────────────

  function _isBlack(midi) {
    return WHITE_KEY_IDX[(midi - START_MIDI) % 12] === -1;
  }

  function _noteGeom(midi) {
    const ww  = _canvas.width / WHITE_TOTAL;
    const bw  = ww * 0.62;
    const oct = Math.floor((midi - START_MIDI) / 12);
    const sem = (midi - START_MIDI) % 12;
    if (!_isBlack(midi)) {
      const wi = WHITE_KEY_IDX[sem];
      return { x: (oct * 7 + wi) * ww + 1, w: ww - 3 };
    }
    const off = BLACK_KEY_OFF[sem];
    return { x: (oct * 7 + off) * ww - bw / 2, w: bw - 1 };
  }

  // ── Audio helpers (countdown ticks) ──────────────────────────────────────────

  function _getAudioCtx() {
    if (!_audioCtx) {
      _audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    return _audioCtx;
  }

  function _playTick(isGo) {
    try {
      const ctx  = _getAudioCtx();
      const osc  = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = isGo ? 880 : 660;
      gain.gain.setValueAtTime(0.25, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.08);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.08);
    } catch (_) { /* AudioContext not available */ }
  }

  // ── Colour helpers ────────────────────────────────────────────────────────────

  function _noteColour(hand, alpha) {
    const rgb = hand === 'left'  ? '79,195,247'
              : hand === 'right' ? '123,109,255'
              : '67,233,123';
    return `rgba(${rgb},${alpha})`;
  }

  // ── Public API ────────────────────────────────────────────────────────────────

  function init() {
    _canvas = document.getElementById('roll-canvas');
    if (!_canvas) return;
    _ctx = _canvas.getContext('2d');
    window.addEventListener('resize', _resize);
    _resize();
  }

  /**
   * Start the roll.
   * @param {Array}    steps        - step objects from ws:lesson_steps
   * @param {number}   bpm          - current BPM
   * @param {string}   [mode]       - 'visual' (default) | 'timed'
   * @param {Function} [onComplete] - timed mode: called with {correct, wrong_steps, total}
   * @param {Function} [onStepChange] - timed mode: called with notes[] when active step changes
   */
  function start(steps, bpm, mode, onComplete, onStepChange) {
    if (!_canvas) return;

    _mode           = mode || 'visual';
    _onComplete     = onComplete || null;
    _onStepChange   = onStepChange || null;
    _bpm            = bpm;
    _done           = false;
    _lastActiveStep = -1;
    _lastTickBeat   = -1;
    _flashMap.clear();

    // Normalise beats so step[0] arrives at hit line at t=0
    const offset = steps.length > 0 ? steps[0].beat : 0;
    _steps = steps.map(s => ({
      beat:     s.beat - offset,
      duration: Math.max(s.duration, 0.1),
      notes:    s.notes,
      hand:     s.hand,
      // timed-mode tracking:
      state:   'upcoming',   // 'upcoming' | 'active' | 'hit' | 'missed'
      pressed: new Set(),
    }));

    // Countdown: _startMs is when beat-0 begins
    const beatMs    = 60000 / _bpm;
    _cdStartMs = Date.now();
    _startMs   = _cdStartMs + COUNTDOWN_BEATS * beatMs;
    _playing   = true;

    if (!_rafId) _rafId = requestAnimationFrame(_draw);
  }

  /** Stop and clear. */
  function stop() {
    _playing        = false;
    _done           = false;
    _lastActiveStep = -1;
    _lastTickBeat   = -1;
    _flashMap.clear();
    if (_rafId) { cancelAnimationFrame(_rafId); _rafId = null; }
    if (_ctx) _drawIdle();
  }

  /**
   * Visual mode: flash a note after engine confirms correct/wrong.
   * Not called in timed mode (Roll.notePressed handles feedback there).
   */
  function noteHit(midi, correct) {
    if (!_playing || _mode !== 'visual') return;
    _flashMap.set(midi, { endMs: Date.now() + FLASH_MS, correct });
  }

  /**
   * Timed mode: called when user presses a key.
   * Returns 'chord_complete' | 'note_accepted' | 'wrong' | null.
   */
  function notePressed(midi) {
    if (!_playing || _mode !== 'timed') return null;
    if (_isInCountdown()) return null;

    const elapsed     = (Date.now() - _startMs) / 1000;
    const currentBeat = elapsed * _bpm / 60;
    const windowBeats = (TIMING_WINDOW_MS / 1000) * (_bpm / 60);

    for (const step of _steps) {
      if (step.state === 'hit' || step.state === 'missed') continue;
      const withinWindow = currentBeat >= step.beat - windowBeats
                        && currentBeat <= step.beat + windowBeats;
      if (!withinWindow) continue;
      if (!step.notes.includes(midi)) continue;

      step.state = 'active';
      step.pressed.add(midi);

      if (step.notes.every(n => step.pressed.has(n))) {
        step.state = 'hit';
        return 'chord_complete';
      }
      return 'note_accepted';
    }

    return 'wrong';
  }

  /** Update BPM mid-lesson, preserving current beat position. */
  function updateBpm(newBpm) {
    if (!_playing) { _bpm = newBpm; return; }
    // Recalculate _startMs so currentBeat is unchanged
    const now         = Date.now();
    const elapsed     = (now - _startMs) / 1000;
    const currentBeat = elapsed * _bpm / 60;
    _bpm     = newBpm;
    _startMs = now - (currentBeat / _bpm) * 60 * 1000;
    // Also shift _cdStartMs proportionally (so countdown length changes too)
    const beatMs = 60000 / _bpm;
    _cdStartMs = _startMs - COUNTDOWN_BEATS * beatMs;
  }

  // ── Internal helpers ─────────────────────────────────────────────────────────

  function _isInCountdown() {
    return Date.now() < _startMs;
  }

  function _resize() {
    if (!_canvas) return;
    _canvas.width  = _canvas.offsetWidth  || (_canvas.parentElement && _canvas.parentElement.clientWidth)  || 800;
    _canvas.height = _canvas.offsetHeight || (_canvas.parentElement && _canvas.parentElement.clientHeight) || 160;
    if (!_playing) _drawIdle();
  }

  function _drawIdle() {
    if (!_ctx) return;
    const w = _canvas.width, h = _canvas.height;
    _ctx.fillStyle = '#0a0a10';
    _ctx.fillRect(0, 0, w, h);
    _drawKeyLines();
    _drawHitLine();
  }

  // ── Main draw loop ────────────────────────────────────────────────────────────

  function _draw() {
    if (!_playing) return;
    _rafId = requestAnimationFrame(_draw);

    const now         = Date.now();
    const w           = _canvas.width;
    const h           = _canvas.height;
    const hitY        = h * HIT_Y_FRAC;
    const elapsed     = (now - _startMs) / 1000;
    const currentBeat = elapsed * _bpm / 60;   // negative during countdown
    const windowBeats = (TIMING_WINDOW_MS / 1000) * (_bpm / 60);

    _ctx.fillStyle = '#0a0a10';
    _ctx.fillRect(0, 0, w, h);
    _drawKeyLines();

    // ── Update timed-mode step states ──
    if (_mode === 'timed' && !_isInCountdown()) {
      for (const step of _steps) {
        if (step.state === 'hit' || step.state === 'missed') continue;
        if (currentBeat > step.beat + windowBeats) {
          step.state = 'missed';
        } else if (currentBeat >= step.beat - windowBeats) {
          if (step.state === 'upcoming') step.state = 'active';
        }
      }

      // Notify hint area when the "next to play" step changes
      if (_onStepChange) {
        let nearestIdx = -1;
        for (let i = 0; i < _steps.length; i++) {
          if (_steps[i].state === 'upcoming' || _steps[i].state === 'active') {
            nearestIdx = i; break;
          }
        }
        if (nearestIdx !== _lastActiveStep) {
          _lastActiveStep = nearestIdx;
          _onStepChange(nearestIdx >= 0 ? _steps[nearestIdx].notes : []);
        }
      }

      // Check completion (all steps resolved)
      if (!_done && _steps.every(s => s.state === 'hit' || s.state === 'missed')) {
        _done = true;
        _finishTimed();
        return;
      }
    }

    // ── Draw note blocks ──
    for (const step of _steps) {
      const noteH      = step.duration * PX_PER_BEAT;
      const noteBottom = hitY - (step.beat - currentBeat) * PX_PER_BEAT;
      const noteTop    = noteBottom - noteH;

      if (noteBottom < -noteH || noteTop > h + noteH) continue;

      for (const midi of step.notes) {
        const { x, w: nw } = _noteGeom(midi);
        _ctx.fillStyle = _stepColour(step, midi, now, currentBeat, hitY, noteBottom);
        _roundRect(x, noteTop, nw, noteH - 2);
      }
    }

    _drawHitLine();

    // ── Countdown overlay ──
    if (_isInCountdown()) {
      const beatMs     = 60000 / _bpm;
      const cdElapsed  = now - _cdStartMs;
      const beatsFired = cdElapsed / beatMs;
      const beatIdx    = Math.floor(beatsFired);  // 0, 1, 2, 3
      const count      = Math.ceil(COUNTDOWN_BEATS - beatsFired);
      const beatFrac   = beatsFired % 1;  // 0→1 within the current beat

      // Fire audio tick once per beat
      if (beatIdx !== _lastTickBeat && beatIdx < COUNTDOWN_BEATS) {
        _lastTickBeat = beatIdx;
        _playTick(count === 1);  // higher pitch on the last countdown beat
      }

      if (count > 0) _drawCountdown(count, beatFrac);
    }

    // visual mode: clean expired flashes
    if (_mode === 'visual') _cleanFlashes(now);
  }

  // ── Colour logic ──────────────────────────────────────────────────────────────

  function _stepColour(step, midi, now, currentBeat, hitY, noteBottom) {
    if (_mode === 'timed') {
      switch (step.state) {
        case 'hit':    return 'rgba(67,233,123,0.75)';
        case 'missed': return 'rgba(255,77,109,0.35)';
        case 'active': return _noteColour(step.hand, 1.0);
        default:       return _noteColour(step.hand, 0.5);
      }
    }

    // Visual mode: flash on hit/wrong, dim for past notes
    const flash = _flashMap.get(midi);
    if (flash && flash.endMs > now) {
      const progress = 1 - (flash.endMs - now) / FLASH_MS;
      return flash.correct
        ? `rgba(67,233,123,${1 - progress * 0.4})`
        : `rgba(255,77,109,${1 - progress * 0.4})`;
    }
    const isPast    = noteBottom < hitY - 2;
    const isCurrent = !isPast && noteBottom <= hitY + step.duration * PX_PER_BEAT;
    if (isPast)    return 'rgba(80,80,120,0.3)';
    if (isCurrent) return _noteColour(step.hand, 0.95);
    return _noteColour(step.hand, 0.55);
  }

  // ── Countdown overlay ─────────────────────────────────────────────────────────

  function _drawCountdown(count, beatFrac) {
    const w = _canvas.width, h = _canvas.height;
    // Subtle darkening behind the number
    _ctx.fillStyle = 'rgba(10,10,16,0.35)';
    _ctx.fillRect(0, 0, w, h);

    // Pulse: starts big at beat onset, shrinks to 1× by beat end
    const scale    = 1.35 - beatFrac * 0.35;
    const fontSize = Math.round(h * 0.52 * scale);

    _ctx.save();
    _ctx.font         = `bold ${fontSize}px 'Segoe UI', system-ui, sans-serif`;
    _ctx.textAlign    = 'center';
    _ctx.textBaseline = 'middle';
    _ctx.shadowColor  = 'rgba(0,0,0,0.9)';
    _ctx.shadowBlur   = 14;
    _ctx.fillStyle    = `rgba(255,220,80,${0.85 + beatFrac * 0.15})`;
    _ctx.fillText(String(count), w / 2, h / 2);
    _ctx.restore();
  }

  // ── Timed completion ──────────────────────────────────────────────────────────

  function _finishTimed() {
    _playing = false;
    cancelAnimationFrame(_rafId);
    _rafId = null;

    // Final frame: draw lingering state
    _draw_final();

    if (_onComplete) {
      const correct     = _steps.filter(s => s.state === 'hit').length;
      const wrong_steps = _steps.filter(s => s.state === 'missed').length;
      _onComplete({ correct, wrong_steps, total: _steps.length });
    }
  }

  function _draw_final() {
    if (!_ctx) return;
    const w = _canvas.width, h = _canvas.height;
    _ctx.fillStyle = '#0a0a10';
    _ctx.fillRect(0, 0, w, h);
    _drawKeyLines();
    // Re-draw steps in their final states
    const hitY = h * HIT_Y_FRAC;
    for (const step of _steps) {
      const noteH      = step.duration * PX_PER_BEAT;
      const noteBottom = hitY;  // all notes at hit line for final view
      const noteTop    = noteBottom - noteH;
      for (const midi of step.notes) {
        const { x, w: nw } = _noteGeom(midi);
        _ctx.fillStyle = step.state === 'hit'
          ? 'rgba(67,233,123,0.5)'
          : 'rgba(255,77,109,0.25)';
        _roundRect(x, noteTop, nw, noteH - 2);
      }
    }
    _drawHitLine();
  }

  // ── Canvas helpers ────────────────────────────────────────────────────────────

  function _drawHitLine() {
    const w = _canvas.width, h = _canvas.height;
    _ctx.fillStyle = 'rgba(255,255,255,0.18)';
    _ctx.fillRect(0, h * HIT_Y_FRAC, w, 2);
  }

  function _drawKeyLines() {
    const w  = _canvas.width, h = _canvas.height;
    const ww = w / WHITE_TOTAL;
    _ctx.fillStyle = 'rgba(46,46,69,0.5)';
    for (let i = 1; i < WHITE_TOTAL; i++) _ctx.fillRect(i * ww, 0, 1, h);
    _ctx.fillStyle = 'rgba(123,109,255,0.06)';
    for (let oct = 0; oct < 5; oct++) _ctx.fillRect(oct * 7 * ww, 0, ww, h);
  }

  function _roundRect(x, y, w, h) {
    const r = Math.min(NOTE_RADIUS, w / 2, Math.max(h / 2, 0));
    if (typeof _ctx.roundRect === 'function') {
      _ctx.beginPath(); _ctx.roundRect(x, y, w, h, r); _ctx.fill();
    } else {
      _ctx.fillRect(x, y, w, h);
    }
  }

  function _cleanFlashes(now) {
    for (const [midi, data] of _flashMap) {
      if (data.endMs <= now) _flashMap.delete(midi);
    }
  }

  return { init, start, stop, noteHit, notePressed, updateBpm };
})();
