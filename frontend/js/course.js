/**
 * course.js — Course progression UI.
 *
 * Renders the sequential curriculum in the sidebar when the "Course" tab is
 * active.  Communicates with the server via the existing WS helper.
 */

const CourseUI = (() => {
  let _state   = null;   // last received course state
  let _onSelect = null;  // callback(lesson_id, hand) when user clicks a step

  // ── Public API ────────────────────────────────────────────────────────────

  function init(onSelectCallback) {
    _onSelect = onSelectCallback;
  }

  /** Render the full course panel from a course state object. */
  function render(courseState) {
    _state = courseState;
    const container = document.getElementById("course-list");
    if (!container) return;

    container.innerHTML = "";

    if (!courseState) {
      container.innerHTML = '<p class="course-empty">Curso não disponível.</p>';
      return;
    }

    const { curriculum, current_index, diagnostic_complete,
            mastery_accuracy, mastery_consecutive } = courseState;

    // Group by stage
    const stages = [];
    let currentStage = null;
    for (const step of curriculum) {
      if (!currentStage || currentStage.name !== step.stage) {
        currentStage = { name: step.stage, steps: [] };
        stages.push(currentStage);
      }
      currentStage.steps.push(step);
    }

    for (const stage of stages) {
      const stageEl = document.createElement("div");
      stageEl.className = "course-stage";

      const heading = document.createElement("div");
      heading.className = "course-stage-heading";
      heading.textContent = stage.name;
      stageEl.appendChild(heading);

      for (const step of stage.steps) {
        stageEl.appendChild(_buildStepEl(step, current_index, mastery_consecutive));
      }

      container.appendChild(stageEl);
    }

    // Update the header stats bar
    _updateStats(courseState);

    // Scroll to current lesson
    const cur = container.querySelector(".course-step.current");
    if (cur) cur.scrollIntoView({ block: "center", behavior: "smooth" });
  }

  /** Highlight the actively playing lesson in the course list. */
  function setActiveLessonId(lessonId, hand) {
    document.querySelectorAll(".course-step").forEach(el => {
      el.classList.toggle(
        "playing",
        el.dataset.lessonId === lessonId && el.dataset.hand === hand
      );
    });
  }

  /** Show attempt feedback banner below the hint area. */
  function showAttemptFeedback(feedback) {
    const banner = document.getElementById("course-feedback");
    if (!banner) return;

    const { passed, consecutive, needed, accuracy, best_accuracy,
            newly_mastered, is_diagnostic } = feedback;

    banner.className = "course-feedback " + (passed ? "pass" : "fail");
    banner.classList.remove("hidden");

    let msg = "";
    if (is_diagnostic) {
      msg = `Diagnóstico completo! Precisão: ${accuracy}%. O teu caminho foi ajustado.`;
    } else if (newly_mastered) {
      msg = `Dominaste esta lição! Próxima desbloqueada.`;
    } else if (passed) {
      const remain = needed - consecutive;
      msg = `Muito bem! ${accuracy}% — ${consecutive}/${needed} passes consecutivos. Mais ${remain} para avançar.`;
    } else {
      const threshold = _state ? _state.mastery_accuracy : 90;
      msg = `${accuracy}% — precisas de ≥${threshold}% para contar como pass. Continua!`;
    }

    banner.textContent = msg;
    clearTimeout(banner._timer);
    banner._timer = setTimeout(() => banner.classList.add("hidden"), 8000);
  }

  // ── Internal helpers ──────────────────────────────────────────────────────

  function _buildStepEl(step, currentIndex, masteryConsecutive) {
    const el = document.createElement("div");
    el.className = "course-step";
    el.dataset.lessonId = step.lesson_id;
    el.dataset.hand     = step.hand;

    const isCurrent  = step.index === currentIndex;
    const isLocked   = !step.unlocked;
    const isMastered = step.mastered;

    if (isCurrent)  el.classList.add("current");
    if (isLocked)   el.classList.add("locked");
    if (isMastered) el.classList.add("mastered");

    // Status icon
    const icon = document.createElement("span");
    icon.className = "step-icon";
    if (isMastered)     icon.textContent = "✓";
    else if (isCurrent) icon.textContent = "▶";
    else if (isLocked)  icon.textContent = "🔒";
    else                icon.textContent = "○";
    el.appendChild(icon);

    // Label
    const label = document.createElement("span");
    label.className = "step-label";
    label.textContent = step.label;
    el.appendChild(label);

    // Hand badge
    const handBadge = document.createElement("span");
    handBadge.className = "step-hand";
    handBadge.textContent = step.hand === "right" ? "MD" : step.hand === "left" ? "ME" : "AM";
    el.appendChild(handBadge);

    // Mastery dots (○○○ → ●●●)
    const dots = document.createElement("span");
    dots.className = "step-dots";
    for (let i = 0; i < masteryConsecutive; i++) {
      const d = document.createElement("span");
      d.className = "step-dot" + (i < step.consecutive ? " filled" : "");
      dots.appendChild(d);
    }
    el.appendChild(dots);

    // Best accuracy
    if (step.attempts > 0) {
      const acc = document.createElement("span");
      acc.className = "step-acc";
      acc.textContent = step.best_accuracy + "%";
      el.appendChild(acc);
    }

    // Click to select (only unlocked lessons)
    if (!isLocked) {
      el.addEventListener("click", () => {
        if (_onSelect) _onSelect(step.lesson_id, step.hand);
      });
    }

    return el;
  }

  function _updateStats(courseState) {
    const bar = document.getElementById("course-stats");
    if (!bar) return;

    const { curriculum, current_index } = courseState;
    const total   = curriculum.length;
    const mastered = curriculum.filter(s => s.mastered).length;
    const pct     = Math.round((mastered / total) * 100);

    bar.innerHTML =
      `<span>${mastered}/${total} dominadas</span>` +
      `<div class="course-progress-bar"><div class="course-progress-fill" style="width:${pct}%"></div></div>` +
      `<span>${pct}%</span>`;
  }

  return { init, render, setActiveLessonId, showAttemptFeedback };
})();
