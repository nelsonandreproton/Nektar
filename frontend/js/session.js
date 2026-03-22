/**
 * session.js — Practice timer and session log.
 * Persists session data to localStorage.
 */
const Session = (() => {
  const STORAGE_KEY = "nektar_sessions";

  let _timerInterval = null;
  let _startTime     = null;   // Date.now() when timer started
  let _elapsedMs     = 0;      // ms accumulated before current start
  let _running       = false;

  // Current session tracking
  let _lessonsPlayed = new Set();
  let _totalCorrect  = 0;
  let _totalWrong    = 0;

  // ── Timer ──────────────────────────────────────────────────────────────────

  function startTimer() {
    if (_running) return;
    _running   = true;
    _startTime = Date.now();
    _timerInterval = setInterval(_tick, 1000);
    _updateTimerDisplay();
    document.getElementById("session-timer").classList.remove("paused");
  }

  function pauseTimer() {
    if (!_running) return;
    _running    = false;
    _elapsedMs += Date.now() - _startTime;
    _startTime  = null;
    clearInterval(_timerInterval);
    document.getElementById("session-timer").classList.add("paused");
  }

  function toggleTimer() {
    if (_running) pauseTimer(); else startTimer();
  }

  function _tick() {
    _updateTimerDisplay();
  }

  function getTotalMs() {
    let total = _elapsedMs;
    if (_running && _startTime) total += Date.now() - _startTime;
    return total;
  }

  function _formatTime(ms) {
    const secs  = Math.floor(ms / 1000);
    const mins  = Math.floor(secs / 60);
    const hours = Math.floor(mins / 60);
    const mm    = String(mins % 60).padStart(2, "0");
    const ss    = String(secs % 60).padStart(2, "0");
    return hours > 0 ? `${hours}:${mm}:${ss}` : `${mm}:${ss}`;
  }

  function _updateTimerDisplay() {
    const el = document.getElementById("session-timer");
    if (el) el.textContent = "⏱ " + _formatTime(getTotalMs());
  }

  // ── Session tracking ───────────────────────────────────────────────────────

  function recordLessonPlayed(lessonId) {
    _lessonsPlayed.add(lessonId);
  }

  function recordResult(correct, wrong) {
    _totalCorrect += correct;
    _totalWrong   += wrong;
  }

  // ── Persistence ────────────────────────────────────────────────────────────

  function _loadSessions() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    } catch { return []; }
  }

  function _saveSessions(sessions) {
    try {
      // Keep at most 30 sessions
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.slice(-30)));
    } catch {}
  }

  function saveCurrentSession() {
    const totalMs = getTotalMs();
    if (totalMs < 30000) return;  // ignore sessions under 30 seconds

    const sessions = _loadSessions();
    const today    = new Date().toISOString().slice(0, 10);

    // Merge into today's entry if it exists
    const existing = sessions.find(s => s.date === today);
    if (existing) {
      existing.duration_ms  += totalMs;
      existing.lessons_played = [...new Set([...existing.lessons_played, ..._lessonsPlayed])];
      existing.correct      += _totalCorrect;
      existing.wrong        += _totalWrong;
    } else {
      sessions.push({
        date:            today,
        duration_ms:     totalMs,
        lessons_played:  [..._lessonsPlayed],
        correct:         _totalCorrect,
        wrong:           _totalWrong,
      });
    }

    _saveSessions(sessions);

    // Reset for next session within same page load
    _elapsedMs     = 0;
    _startTime     = _running ? Date.now() : null;
    _lessonsPlayed = new Set();
    _totalCorrect  = 0;
    _totalWrong    = 0;
  }

  // ── Log panel rendering ────────────────────────────────────────────────────

  function renderLog() {
    const sessions = _loadSessions();
    const today    = new Date().toISOString().slice(0, 10);

    // Today's stats
    const todaySess   = sessions.find(s => s.date === today);
    const todayMs     = (todaySess?.duration_ms || 0) + getTotalMs();
    const totalAllMs  = sessions.reduce((a, s) => a + s.duration_ms, 0) + getTotalMs();

    document.getElementById("stat-today-time").textContent = _minStr(todayMs);
    document.getElementById("stat-total-time").textContent = _minStr(totalAllMs);

    // Streak
    let streak = 0;
    const dateSet = new Set(sessions.map(s => s.date));
    let d = new Date();
    while (true) {
      const ds = d.toISOString().slice(0, 10);
      if (!dateSet.has(ds) && ds !== today) break;
      if (dateSet.has(ds) || ds === today) streak++;
      d.setDate(d.getDate() - 1);
    }
    document.getElementById("stat-streak").textContent = streak;

    // History list (most recent first)
    const histEl = document.getElementById("session-history");
    histEl.innerHTML = "";
    [...sessions].reverse().forEach(s => {
      const el = document.createElement("div");
      el.className = "session-entry";
      el.innerHTML = `
        <span class="s-date">${s.date}</span>
        <span class="s-lessons">${s.lessons_played.length} lesson${s.lessons_played.length !== 1 ? "s" : ""}</span>
        <span>${_minStr(s.duration_ms)}</span>
      `;
      histEl.appendChild(el);
    });

    if (sessions.length === 0) {
      histEl.innerHTML = '<div style="text-align:center;color:var(--muted);font-size:12px;padding:8px">No sessions yet</div>';
    }
  }

  function clearHistory() {
    if (confirm("Clear all session history?")) {
      localStorage.removeItem(STORAGE_KEY);
      renderLog();
    }
  }

  function _minStr(ms) {
    const m = Math.floor(ms / 60000);
    return m < 60 ? `${m} min` : `${Math.floor(m / 60)}h ${m % 60}m`;
  }

  // ── Auto-save on page unload ───────────────────────────────────────────────

  window.addEventListener("beforeunload", saveCurrentSession);

  // ── DOM wiring ────────────────────────────────────────────────────────────

  document.addEventListener("DOMContentLoaded", () => {
    // Click timer to pause/resume
    const timerEl = document.getElementById("session-timer");
    if (timerEl) timerEl.addEventListener("click", toggleTimer);

    // Session log panel
    const logBtn   = document.getElementById("btn-session-log");
    const panel    = document.getElementById("session-panel");
    const closeBtn = document.getElementById("btn-session-close");
    const clearBtn = document.getElementById("btn-clear-session");

    if (logBtn && panel) {
      logBtn.addEventListener("click", () => {
        renderLog();
        panel.classList.toggle("hidden");
      });
    }
    if (closeBtn && panel) closeBtn.addEventListener("click", () => panel.classList.add("hidden"));
    if (clearBtn) clearBtn.addEventListener("click", clearHistory);

    // Auto-start timer when a lesson starts
    window.addEventListener("ws:open", () => startTimer());

    _updateTimerDisplay();
  });

  return {
    startTimer,
    pauseTimer,
    toggleTimer,
    recordLessonPlayed,
    recordResult,
    saveCurrentSession,
    isRunning: () => _running,
  };
})();
