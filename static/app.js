let topics = [];
let exercises = [];
let practiceTests = [];
let selectedTopicId = null;
let selectedExercise = null;
let vizDrag = { active: false, startX: 0, startY: 0 };
let codePopupDrag = { active: false, startX: 0, startY: 0 };

const els = {
  topicList: document.querySelector("#topicList"),
  search: document.querySelector("#search"),
  track: document.querySelector("#track"),
  title: document.querySelector("#title"),
  level: document.querySelector("#level"),
  intro: document.querySelector("#intro"),
  mentalModel: document.querySelector("#mentalModel"),
  learningOutcome: document.querySelector("#learningOutcome"),
  lessonSections: document.querySelector("#lessonSections"),
  syntax: document.querySelector("#syntax"),
  example: document.querySelector("#example"),
  realWorld: document.querySelector("#realWorld"),
  mustKnow: document.querySelector("#mustKnow"),
  commonTraps: document.querySelector("#commonTraps"),
  interview: document.querySelector("#interview"),
  docs: document.querySelector("#docs"),
  exerciseSelect: document.querySelector("#exerciseSelect"),
  exerciseTitle: document.querySelector("#exerciseTitle"),
  exercisePrompt: document.querySelector("#exercisePrompt"),
  editor: document.querySelector("#editor"),
  testOutput: document.querySelector("#testOutput"),
  aiOutput: document.querySelector("#aiOutput"),
  coachInput: document.querySelector("#coachInput"),
  coachStatus: document.querySelector("#coachStatus"),
  runBtn: document.querySelector("#runBtn"),
  aiBtn: document.querySelector("#aiBtn"),
  explainBtn: document.querySelector("#explainBtn"),
  resetBtn: document.querySelector("#resetBtn"),
  hintBtn: document.querySelector("#hintBtn"),
  solutionBtn: document.querySelector("#solutionBtn"),
  provider: document.querySelector("#provider"),
  model: document.querySelector("#model"),
  modelSelect: document.querySelector("#modelSelect"),
  refreshModelsBtn: document.querySelector("#refreshModelsBtn"),
  modelHelpText: document.querySelector("#modelHelpText"),
  endpoint: document.querySelector("#endpoint"),
  apiKey: document.querySelector("#apiKey"),
  apiKeyFieldLabel: document.querySelector("#apiKeyFieldLabel"),
  apiKeyHelpText: document.querySelector("#apiKeyHelpText"),
  practiceQuestions: document.querySelector("#practiceQuestions"),
  checkTestBtn: document.querySelector("#checkTestBtn"),
  resetTestBtn: document.querySelector("#resetTestBtn"),
  checkTestBtnBottom: document.querySelector("#checkTestBtnBottom"),
  resetTestBtnBottom: document.querySelector("#resetTestBtnBottom"),
  testResult: document.querySelector("#testResult"),
  scratchpad: document.querySelector("#scratchpad"),
  scratchToggle: document.querySelector("#scratchToggle"),
  scratchBody: document.querySelector("#scratchBody"),
  scratchEditor: document.querySelector("#scratchEditor"),
  scratchRunBtn: document.querySelector("#scratchRunBtn"),
  scratchVizBtn: document.querySelector("#scratchVizBtn"),
  scratchClearBtn: document.querySelector("#scratchClearBtn"),
  scratchOutput: document.querySelector("#scratchOutput"),
  labVizBtn: document.querySelector("#labVizBtn"),
  vizOverlay: document.querySelector("#vizOverlay"),
  vizModal: document.querySelector(".viz-modal"),
  vizModalHead: document.querySelector(".viz-modal-head"),
  vizAskAiBtn: document.querySelector("#vizAskAiBtn"),
  vizCode: document.querySelector("#vizCode"),
  vizVarList: document.querySelector("#vizVarList"),
  vizNote: document.querySelector("#vizNote"),
  vizPrev: document.querySelector("#vizPrev"),
  vizNext: document.querySelector("#vizNext"),
  vizCount: document.querySelector("#vizCount"),
  vizClose: document.querySelector("#vizClose"),
  codePopup: document.querySelector("#codePopup"),
  codePopupModal: document.querySelector("#codePopupModal"),
  codePopupHeader: document.querySelector(".code-popup-header"),
  codePopupMaxBtn: document.querySelector("#codePopupMaxBtn"),
  codePopupClose: document.querySelector("#codePopupClose"),
  codePopupEditor: document.querySelector("#codePopupEditor"),
  codePopupRunBtn: document.querySelector("#codePopupRunBtn"),
  codePopupVizBtn: document.querySelector("#codePopupVizBtn"),
  codePopupAiBtn: document.querySelector("#codePopupAiBtn"),
  codePopupClearBtn: document.querySelector("#codePopupClearBtn"),
  codePopupOutput: document.querySelector("#codePopupOutput"),
  askAiDock: document.querySelector("#askAiDock"),
  askAiPanel: document.querySelector("#askAiPanel"),
  askAiClose: document.querySelector("#askAiClose"),
  askAiMinimize: document.querySelector("#askAiMinimize"),
  askAiMaximize: document.querySelector("#askAiMaximize"),
  askAiNewChat: document.querySelector("#askAiNewChat"),
  askAiSessionTabs: document.querySelector("#askAiSessionTabs"),
  askAiLauncher: document.querySelector("#askAiLauncher"),
  askAiLauncherStatus: document.querySelector("#askAiLauncherStatus"),
  askAiOutput: document.querySelector("#askAiOutput"),
  askAiInput: document.querySelector("#askAiInput"),
  askAiStatus: document.querySelector("#askAiStatus"),
  askAiSendBtn: document.querySelector("#askAiSendBtn"),
};

let lastRunResult = null;
let preferredModel = "";
let coachMessages = [];
const ASK_AI_WELCOME_MESSAGE = "Need a quick explanation? Ask about highlighted text, a lesson idea, a Try It example, or a visualizer step. I can break it down, give a small example, or connect it to what you are learning.";
let askAiMessages = [{ role: "assistant", text: ASK_AI_WELCOME_MESSAGE }];
// Ask AI supports parallel chat sessions (like separate messenger threads):
// each session keeps its own message array so "New chat" never erases another
// conversation. askAiMessages always points at the active session's array.
let askAiSessionSeq = 1;
let activeAskAiSessionId = askAiSessionSeq;
let askAiSessions = [{ id: askAiSessionSeq, title: "New chat", messages: askAiMessages }];
const MESSAGE_TYPE_INTERVAL_MS = 24;
const MESSAGE_TYPE_CHUNK_SIZE = 2;
let coachTypingTimer = null;
let askAiTypingTimer = null;
// Bumped whenever the AI Coach transcript or Ask AI chat is reset (exercise
// switch, New chat). In-flight streams capture the value at start and check
// it before writing into coachMessages/askAiMessages, so a late chunk from a
// stale request cannot land in a different conversation.
let coachStreamGen = 0;
let askAiStreamGen = 0;
const LOCAL_AI_PROVIDERS = new Set(["ollama", "lmstudio"]);
let aiSettingsKeyPresent = false;
let solutionRevealed = false;
let failedAttempts = 0;
const AI_REQUEST_TIMEOUT_MS = 52000;
const AI_PROVIDER_TEST_TIMEOUT_MS = 25000;
// ---------------------------------------------------------------------------
// Progress tracking (localStorage)
// ---------------------------------------------------------------------------

function loadProgress() {
  try {
    return JSON.parse(localStorage.getItem("pySkillLabProgress") || "{}");
  } catch {
    return {};
  }
}

function saveProgress(progress) {
  localStorage.setItem("pySkillLabProgress", JSON.stringify(progress));
}

function markTopicVisited(topicId) {
  const progress = loadProgress();
  if (!progress[topicId]) progress[topicId] = {};
  progress[topicId].visited = true;
  progress[topicId].lastVisit = Date.now();
  progress._lastTopicId = topicId;  // persist for "continue where you left off"
  saveProgress(progress);
}

function markExercisePassed(exerciseId) {
  const progress = loadProgress();
  if (!progress.exercises) progress.exercises = {};
  progress.exercises[exerciseId] = { passed: true, date: Date.now() };
  saveProgress(progress);
}

function practiceContentHash(questions) {
  const canonical = JSON.stringify((questions || []).map((q) => ({
    question: q.question || "",
    options: (q.options || []).map((option) => String(option)),
    answer: q.answer,
    explanation: q.explanation || "",
  })));
  let hash = 2166136261;
  for (let i = 0; i < canonical.length; i += 1) {
    hash = Math.imul(hash ^ canonical.charCodeAt(i), 16777619) >>> 0;
  }
  return `${questions.length}:${hash.toString(16)}`;
}

function markTestScore(topicId, score, total, questions) {
  const progress = loadProgress();
  if (!progress[topicId]) progress[topicId] = {};
  progress[topicId].testScore = score;
  progress[topicId].testTotal = total;
  if (questions && questions.length) {
    progress[topicId].practiceHash = practiceContentHash(questions);
    // Retakes are intentional: readiness reflects the latest submitted attempt.
    progress[topicId].practiceSubmitted = true;
  }
  saveProgress(progress);
}

function resetPracticeProgress(topicId) {
  const progress = loadProgress();
  if (!progress[topicId]) return;
  delete progress[topicId].testScore;
  delete progress[topicId].testTotal;
  delete progress[topicId].practiceHash;
  delete progress[topicId].practiceSubmitted;
  saveProgress(progress);
}

function setRetakeButtonsVisible(visible) {
  [els.resetTestBtn, els.resetTestBtnBottom].forEach((button) => {
    if (button) button.hidden = !visible;
  });
}

function setPracticeCheckButtonsEnabled(enabled) {
  [els.checkTestBtn, els.checkTestBtnBottom].forEach((button) => {
    if (button) button.disabled = !enabled;
  });
}

function getTopicProgress(topicId) {
  const progress = loadProgress();
  const tp = progress[topicId] || {};
  // Invalidate stale practice score if content has changed
  if (tp.practiceHash !== undefined && practiceTests) {
    const test = practiceTests.find(t => t.topic_id === topicId);
    const questions = test ? (test.questions || []) : [];
    if (questions.length && practiceContentHash(questions) !== tp.practiceHash) {
      const { testScore, testTotal, practiceHash, practiceSubmitted, ...rest } = tp;
      progress[topicId] = rest;
      saveProgress(progress);
      return rest;
    }
  }
  return tp;
}

function isExercisePassed(exerciseId) {
  const progress = loadProgress();
  return progress.exercises && progress.exercises[exerciseId] && progress.exercises[exerciseId].passed;
}

function getTopicLabStats(topicId) {
  const topicExercises = exercises.filter((ex) => ex.topic_id === topicId);
  const coreLabs = topicExercises.filter((ex) => ex.difficulty !== "Advanced");
  const capstones = topicExercises.filter((ex) => ex.difficulty === "Advanced");
  const corePassed = coreLabs.filter((ex) => isExercisePassed(ex.id)).length;
  const capstonePassed = capstones.filter((ex) => isExercisePassed(ex.id)).length;
  return {
    corePassed,
    coreTotal: coreLabs.length,
    capstonePassed,
    capstoneTotal: capstones.length,
    passed: corePassed,
    total: topicExercises.length,
    required: coreLabs.length,
  };
}

function getTopicReadiness(topicId) {
  const labs = getTopicLabStats(topicId);
  const tp = getTopicProgress(topicId);
  const testPct = tp.testTotal ? tp.testScore / tp.testTotal : null;
  const testPassed = testPct !== null && testPct >= 0.8;
  const coreDone = labs.coreTotal === 0 || labs.corePassed >= labs.coreTotal;
  const capstoneDone = labs.capstoneTotal === 0 || labs.capstonePassed >= labs.capstoneTotal;
  const isReady = testPassed && coreDone;
  const coreRatio = labs.coreTotal ? labs.corePassed / labs.coreTotal : 1;
  const hasCapstone = labs.capstoneTotal > 0;
  const coreWeight = hasCapstone ? 0.6 : 0.7;
  const practiceWeight = hasCapstone ? 0.25 : 0.3;
  const capstoneWeight = hasCapstone ? 0.15 : 0;
  const practiceRatio = testPct !== null ? testPct : 0;
  const progressPct = Math.round((
    (coreRatio * coreWeight) +
    (practiceRatio * practiceWeight) +
    (hasCapstone && capstoneDone ? capstoneWeight : 0)
  ) * 100);
  return {
    ...labs,
    testScore: tp.testScore,
    testTotal: tp.testTotal,
    testPct,
    testPassed,
    coreDone,
    capstoneDone,
    hasCapstone,
    isReady,
    progressPct,
  };
}

// ---------------------------------------------------------------------------
// Code draft auto-save
// ---------------------------------------------------------------------------

function saveDraft(exerciseId, code) {
  try {
    const drafts = JSON.parse(localStorage.getItem("pySkillLabDrafts") || "{}");
    drafts[exerciseId] = code;
    localStorage.setItem("pySkillLabDrafts", JSON.stringify(drafts));
  } catch { /* ignore */ }
}

function loadDraft(exerciseId) {
  try {
    const drafts = JSON.parse(localStorage.getItem("pySkillLabDrafts") || "{}");
    return drafts[exerciseId] || null;
  } catch {
    return null;
  }
}

function clearDraft(exerciseId) {
  try {
    const drafts = JSON.parse(localStorage.getItem("pySkillLabDrafts") || "{}");
    delete drafts[exerciseId];
    localStorage.setItem("pySkillLabDrafts", JSON.stringify(drafts));
  } catch { /* ignore */ }
}

async function postJsonWithTimeout(url, payload, timeoutMs = 0) {
  const controller = timeoutMs > 0 ? new AbortController() : null;
  const timer = controller ? setTimeout(() => controller.abort(), timeoutMs) : null;
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller ? controller.signal : undefined,
    });
    let data = {};
    try {
      data = await response.json();
    } catch {
      data = {};
    }
    if (!response.ok) {
      data.ok = false;
      if (!data.error) {
        data.error = `HTTP ${response.status} ${response.statusText}`;
      }
    }
    return data;
  } catch (error) {
    if (error && error.name === "AbortError") {
      throw new Error(`timed out after ${Math.round(timeoutMs / 1000)}s`);
    }
    throw error;
  } finally {
    if (timer) clearTimeout(timer);
  }
}

async function postAiStreamWithTimeout(payload, callbacks = {}, timeoutMs = 0) {
  const controller = timeoutMs > 0 ? new AbortController() : null;
  const timer = controller ? setTimeout(() => controller.abort(), timeoutMs) : null;
  let streamedAnswer = "";
  try {
    const response = await fetch("/api/ai-coach-stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller ? controller.signal : undefined,
    });
    if (!response.ok || !response.body) {
      const fallback = await postJsonWithTimeout("/api/ai-coach", payload, timeoutMs);
      callbacks.onFallback?.(fallback);
      return fallback;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        const event = JSON.parse(trimmed);
        if (event.type === "chunk") {
          streamedAnswer += event.text || "";
          callbacks.onChunk?.(streamedAnswer, event.text || "");
        } else if (event.type === "done") {
          const result = {
            ok: event.ok !== false,
            answer: event.text || event.answer || streamedAnswer,
            error: event.error || "",
            tokens_in: event.tokens_in || 0,
            tokens_out: event.tokens_out || 0,
            elapsed_sec: event.elapsed_sec || 0,
            tok_per_sec: event.tok_per_sec || 0,
            streamed: streamedAnswer.length > 0,
          };
          callbacks.onDone?.(result);
          return result;
        }
      }
    }

    const result = { ok: true, answer: streamedAnswer, streamed: streamedAnswer.length > 0 };
    callbacks.onDone?.(result);
    return result;
  } catch (error) {
    if (error && error.name === "AbortError") {
      throw new Error(`timed out after ${Math.round(timeoutMs / 1000)}s`);
    }
    throw error;
  } finally {
    if (timer) clearTimeout(timer);
  }
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

async function boot() {
  try {
    const response = await fetch("/api/curriculum");
    if (!response.ok) throw new Error(`server responded ${response.status}`);
    const data = await response.json();
    topics = data.topics || [];
    exercises = data.exercises || [];
    practiceTests = data.practice_tests || [];
    if (!topics.length) throw new Error("no topics were returned");

    // Restore last visited topic ("continue where you left off")
    const progress = loadProgress();
    const lastTopicId = progress._lastTopicId;
    const validLastTopic = lastTopicId && topics.find((t) => t.id === lastTopicId);
    selectedTopicId = validLastTopic ? lastTopicId : topics[0].id;

    renderTopicList();
    selectTopic(selectedTopicId);

    // Spaced repetition: nudge for topics not visited in 7+ days
    checkSpacedRepetitionNudges(progress);
  } catch (error) {
    showBootError(error);
  }
}

/** Replace the blank workspace with a clear, non-technical failure message. */
function showBootError(error) {
  const workspace = document.querySelector(".workspace");
  if (!workspace) return;
  const panel = document.createElement("div");
  panel.className = "boot-error";
  panel.setAttribute("role", "alert");
  panel.innerHTML = `
    <h2>The lessons could not load</h2>
    <p>The app started but could not read its curriculum from the local server.</p>
    <p>Make sure <code>python app.py</code> is still running, then reload this page. If it keeps
    failing, restart the server from the project folder.</p>
    <p class="boot-error-detail">Details: ${escapeHtml(String(error))}</p>
  `;
  workspace.prepend(panel);
}

/** Show one review nudge for any topic not practiced in 7+ days. */
function checkSpacedRepetitionNudges(progress) {
  const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;
  const now = Date.now();
  const stale = topics.filter((topic) => {
    const tp = progress[topic.id];
    return tp && tp.lastVisit && now - tp.lastVisit > SEVEN_DAYS_MS;
  });
  if (!stale.length) return;

  // Pick the most recently studied of the stale topics
  const oldest = stale.sort((a, b) => progress[a.id].lastVisit - progress[b.id].lastVisit)[0];
  const days = Math.floor((now - progress[oldest.id].lastVisit) / (24 * 60 * 60 * 1000));

  showReviewNudge(oldest, days);
}

function showReviewNudge(topic, days) {
  const banner = document.createElement("div");
  banner.className = "review-nudge";
  banner.setAttribute("role", "alert");
  banner.innerHTML = `
    <span class="nudge-icon">🔁</span>
    <span>You studied <strong>${escapeHtml(topic.title)}</strong> ${days} day${days !== 1 ? 's' : ''} ago — a quick review helps retention.</span>
    <div class="nudge-actions">
      <button type="button" onclick="selectTopic('${topic.id}');this.closest('.review-nudge').remove()" class="nudge-btn">Review now</button>
      <button type="button" onclick="this.closest('.review-nudge').remove()" class="nudge-dismiss" aria-label="Dismiss">✕</button>
    </div>
  `;
  document.querySelector(".workspace").prepend(banner);
  // Auto-dismiss after 12 seconds
  setTimeout(() => banner.remove(), 12000);
}

/**
 * True when the learner has set up an AI provider they can actually use.
 * Hosted providers need a key (or a saved model); local providers need a
 * chosen model. Used to decide whether to show first-run AI onboarding.
 */
function isAiConfigured() {
  const model = (els.model.value || "").trim();
  if (isLocalAiProvider()) return !!model;
  return aiSettingsKeyPresent || !!model;
}

/**
 * First-run nudge: a beginner with no AI configured otherwise meets a cryptic
 * provider error on their first "Ask AI" click. Show one dismissible banner
 * pointing at AI Settings, at most once until they configure AI or dismiss it.
 */
function maybeShowAiOnboarding() {
  if (isAiConfigured()) return;
  if (localStorage.getItem("pySkillLabAiOnboarded") === "1") return;
  const workspace = document.querySelector(".workspace");
  if (!workspace || workspace.querySelector(".ai-onboard-nudge")) return;

  const banner = document.createElement("div");
  banner.className = "review-nudge ai-onboard-nudge";
  banner.setAttribute("role", "note");
  banner.innerHTML = `
    <span class="nudge-icon">🤖</span>
    <span>The <strong>AI Coach</strong> is optional and needs a one-time setup. Easiest: pick a hosted
    provider (OpenAI, Anthropic, Google, or Groq) and paste an API key — no install. You can also run
    it fully offline with Ollama.</span>
    <div class="nudge-actions">
      <button type="button" id="aiOnboardOpenBtn" class="nudge-btn">Open AI Settings</button>
      <button type="button" class="nudge-dismiss" aria-label="Dismiss" onclick="localStorage.setItem('pySkillLabAiOnboarded','1');this.closest('.ai-onboard-nudge').remove()">✕</button>
    </div>
  `;
  workspace.prepend(banner);
  const openBtn = banner.querySelector("#aiOnboardOpenBtn");
  if (openBtn) {
    openBtn.addEventListener("click", () => {
      localStorage.setItem("pySkillLabAiOnboarded", "1");
      banner.remove();
      const settingsBtn = document.getElementById("aiSettingsBtn");
      if (settingsBtn) settingsBtn.click();
    });
  }
}

// ---------------------------------------------------------------------------
// Topic list & navigation
// ---------------------------------------------------------------------------

function renderTopicList() {
  const query = els.search.value.trim().toLowerCase();
  const progress = loadProgress();
  els.topicList.innerHTML = "";

  const filteredTopics = topics.filter((topic) => {
    const titleTrack = `${topic.title} ${topic.track}`.toLowerCase();
    const intro = topic.intro.toLowerCase();
    return titleTrack.includes(query) || intro.includes(query);
  }).sort((a, b) => {
    const aScore = `${a.title} ${a.track}`.toLowerCase().includes(query) ? 1 : 0;
    const bScore = `${b.title} ${b.track}`.toLowerCase().includes(query) ? 1 : 0;
    return bScore - aScore;
  });

  if (filteredTopics.length === 0 && query) {
    els.topicList.innerHTML = `<p class="topic-search-empty">No topics match "<strong>${escapeHtml(query)}</strong>". <button type="button" class="topic-search-clear">Clear</button></p>`;
    els.topicList.querySelector('.topic-search-clear')?.addEventListener('click', () => {
      els.search.value = '';
      renderTopicList();
    });
    return;
  }

  let currentTrack = "";
  filteredTopics
    .forEach((topic) => {
      // Track separator
      if (topic.track !== currentTrack) {
        currentTrack = topic.track;
        const trackHeader = document.createElement("div");
        trackHeader.className = "track-header";
        trackHeader.textContent = currentTrack;
        els.topicList.appendChild(trackHeader);
      }

      const button = document.createElement("button");
      button.className = `topic-button ${topic.id === selectedTopicId ? "active" : ""}`;
      button.type = "button";

      const topicProgress = progress[topic.id] || {};
      const r = getTopicReadiness(topic.id);
      let badge = "";
      if (r.isReady) {
        badge = r.capstoneDone
          ? `<span class="progress-badge badge-ready" title="Topic complete">Done</span>`
          : `<span class="progress-badge badge-pass" title="Core labs and practice passed; capstone pending">Core ready</span>`;
      } else if (r.corePassed > 0 || r.testScore !== undefined) {
        const parts = [];
        if (r.corePassed > 0) parts.push(`Core ${r.corePassed}/${r.coreTotal}`);
        if (r.testScore !== undefined) parts.push(`Practice ${Math.round(r.testPct * 100)}%`);
        badge = `<span class="progress-badge badge-partial">${parts.join(" · ")}</span>`;
      } else if (topicProgress.visited) {
        badge = `<span class="progress-badge badge-visited">Started</span>`;
      }

      button.innerHTML = `<span>${topic.track}</span>${escapeHtml(topic.title)}${badge}`;
      button.addEventListener("click", () => selectTopic(topic.id));
      els.topicList.appendChild(button);
    });
}

function selectTopic(topicId) {
  selectedTopicId = topicId;
  const topic = topics.find((item) => item.id === topicId);
  els.track.textContent = topic.track;
  els.title.textContent = topic.title;
  els.level.textContent = topic.level;
  els.intro.textContent = topic.intro;
  els.mentalModel.textContent = topic.mental_model || "";
  els.learningOutcome.textContent = topic.outcome || buildLearningOutcome(topic);
  els.lessonSections.innerHTML = renderLessonSections(topic.lesson_sections || []);
  const askAiLessonBtn = document.createElement("button");
  askAiLessonBtn.type = "button";
  askAiLessonBtn.className = "ask-ai-lesson-btn";
  askAiLessonBtn.textContent = "Ask AI about this lesson";
  askAiLessonBtn.addEventListener("click", () => {
    askFloatingAi(
      `Explain the "${topic.title}" lesson to me with a simple real-world analogy and a code example.`,
      { includeTopicContext: true }
    );
  });
  els.lessonSections.appendChild(askAiLessonBtn);
  els.syntax.textContent = topic.syntax;
  els.example.textContent = topic.example;
  els.realWorld.innerHTML = renderList(topic.real_world || []);
  els.mustKnow.innerHTML = renderList(topic.must_know || []);
  els.commonTraps.innerHTML = renderList(topic.common_traps || []);
  els.interview.innerHTML = renderList(topic.interview || []);
  els.docs.innerHTML = (topic.docs || [])
    .map((doc) => `<li><a href="${escapeHtml(doc.url)}" target="_blank" rel="noreferrer">${escapeHtml(doc.label)}</a></li>`)
    .join("");
  renderTopicList();
  renderExercises(topicId);
  renderPracticeTest(topicId);
  setActiveTopicSection("overviewSection");
  markTopicVisited(topicId);
  // On narrow screens, collapse the topic list so the workspace is immediately visible
  if (window.innerWidth <= 1020) _collapseTopicList();
}

function buildLearningOutcome(topic) {
  const firstSkill = topic.must_know && topic.must_know[0] ? topic.must_know[0] : "explain the core idea clearly";
  return `After this topic, you should be able to use the concept in a small program, recognize where it appears in real work, avoid common mistakes, and explain this skill clearly. First checkpoint: ${firstSkill}`;
}

function renderList(items) {
  // Coerce non-arrays (e.g. a content field authored as a string) so a single
  // malformed field can never crash the whole topic render.
  if (!Array.isArray(items)) items = items ? [items] : [];
  return items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function _lessonTipCard() {
  if (localStorage.getItem("pySkillLabTipDismissed")) return "";
  return `
    <div class="lesson-tip-card" id="lessonTipCard">
      <span class="lesson-tip-icon">ⓘ</span>
      <span class="lesson-tip-text">
        <strong>▶ Try it</strong> — hover any code block to run it in a popup without leaving this page &nbsp;·&nbsp;
        <strong>Ask AI</strong> — select any text on the page, then click the floating button for a simpler explanation
      </span>
      <button type="button" class="lesson-tip-dismiss" aria-label="Dismiss tip">✕</button>
    </div>`;
}

function renderLessonSections(sections) {
  if (!sections.length) return "";
  const tipCard = _lessonTipCard();
  return tipCard + sections
    .map(
      (section) => {
        const sourceLink = section.source_url
          ? `<a class="section-source" href="${escapeHtml(section.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(section.source_label || "Official source")}</a>`
          : "";
        // diagram_svg is trusted, author-written content (never user/AI input),
        // so it is rendered inline as-is. Do not feed external text into this field.
        const diagram = section.diagram_svg
          ? `<figure class="section-diagram">${section.diagram_svg}${
              section.diagram_caption ? `<figcaption>${escapeHtml(section.diagram_caption)}</figcaption>` : ""
            }</figure>`
          : "";
        return `
          <article class="lesson-section-card">
            <h3>${escapeHtml(section.title)}</h3>
            <div class="section-body">${renderLessonMarkdown(section.body || '')}</div>
            ${diagram}
            ${sourceLink}
          </article>
        `;
      }
    )
    .join("");
}

// ---------------------------------------------------------------------------
// Exercises
// ---------------------------------------------------------------------------

function renderExercises(topicId) {
  const topicExercises = exercises.filter((exercise) => exercise.topic_id === topicId);

  if (!topicExercises.length) {
    els.exerciseSelect.innerHTML = '<option value="">No exercises yet for this topic</option>';
    els.exerciseTitle.textContent = "Coming Soon";
    els.exercisePrompt.textContent = "Exercises for this topic are being developed. Check back later or explore the lesson and practice test.";
    els.editor.value = "# No exercise available for this topic yet.\n# Try the Practice Test tab instead!\n";
    els.editor.disabled = true;
    els.testOutput.textContent = "No exercises available.";
    return;
  }

  els.editor.disabled = false;
  els.exerciseSelect.innerHTML = topicExercises
    .map((exercise) => {
      const passed = isExercisePassed(exercise.id);
      const icon = passed ? "✓ " : "";
      return `<option value="${exercise.id}">${icon}${escapeHtml(exercise.title)}</option>`;
    })
    .join("");
  selectExercise(topicExercises[0].id);
}

function renderPracticeTest(topicId) {
  const test = practiceTests.find((item) => item.topic_id === topicId);
  const questions = test ? test.questions : [];
  if (!questions.length) {
    els.practiceQuestions.innerHTML = "<p>No practice test is available yet for this topic.</p>";
    els.testResult.textContent = "Nothing to check yet.";
    return;
  }

  els.practiceQuestions.innerHTML = questions
    .map((question, questionIndex) => {
      const options = question.options
        .map(
          (option, optionIndex) => `
            <label class="answer-option">
              <input type="radio" name="question-${questionIndex}" value="${optionIndex}" />
              <span>${_inlineMarkdown(option)}</span>
            </label>
          `
        )
        .join("");
      return `
        <article class="question-card" data-question-index="${questionIndex}">
          <h4>${questionIndex + 1}. ${_inlineMarkdown(question.question)}</h4>
          <div class="answer-options">${options}</div>
          <p class="answer-explanation"></p>
        </article>
      `;
    })
    .join("");

  const tp = getTopicProgress(topicId);
  if (tp.practiceSubmitted) {
    // Restore locked state after page refresh — score is already recorded
    document.querySelectorAll('.answer-options input[type="radio"]').forEach(r => { r.disabled = true; });
    els.testResult.textContent = tp.testTotal
      ? `Score: ${tp.testScore}/${tp.testTotal} (submitted)`
      : "You have already submitted this test.";
    setRetakeButtonsVisible(true);
    setPracticeCheckButtonsEnabled(false);
  } else {
    els.testResult.textContent = "Choose an answer, then check your result.";
    setRetakeButtonsVisible(false);
    setPracticeCheckButtonsEnabled(true);
  }
}

function checkPracticeTest() {
  const test = practiceTests.find((item) => item.topic_id === selectedTopicId);
  const questions = test ? test.questions : [];
  if (!questions.length) return;

  // Block accidental double-submit; learners can use Retake Test to start over.
  const tp = getTopicProgress(selectedTopicId);
  if (tp.practiceSubmitted) {
    els.testResult.textContent = "You have already submitted this attempt. Use Retake Test to try again.";
    return;
  }

  document.querySelectorAll('.unanswered-highlight').forEach((c) => c.classList.remove('unanswered-highlight'));
  const unansweredIndexes = questions
    .map((_, i) => i)
    .filter((i) => !document.querySelector(`input[name="question-${i}"]:checked`));
  if (unansweredIndexes.length) {
    const unanswered = unansweredIndexes.length;
    els.testResult.textContent = `${unanswered} question${unanswered > 1 ? "s" : ""} unanswered — please answer all before checking.`;
    unansweredIndexes.forEach((i) => {
      const card = document.querySelector(`[data-question-index="${i}"]`);
      if (card) card.classList.add('unanswered-highlight');
    });
    const firstCard = document.querySelector(`[data-question-index="${unansweredIndexes[0]}"]`);
    if (firstCard) firstCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }

  let score = 0;
  questions.forEach((question, questionIndex) => {
    const card = document.querySelector(`[data-question-index="${questionIndex}"]`);
    const selected = document.querySelector(`input[name="question-${questionIndex}"]:checked`);
    const selectedValue = selected ? Number(selected.value) : -1;
    const correct = selectedValue === question.answer;
    if (correct) score += 1;
    card.classList.toggle("correct", correct);
    card.classList.toggle("incorrect", !correct);
    // Option-level feedback: mark selected wrong answer and correct answer
    card.querySelectorAll('.answer-option').forEach((lbl, idx) => {
      lbl.classList.toggle('option-selected-wrong', !correct && idx === selectedValue);
      lbl.classList.toggle('option-correct', idx === question.answer);
    });
    const explanationEl = card.querySelector(".answer-explanation");
    // _inlineMarkdown escapes HTML and renders `code`/**bold**, so backticks in
    // explanations show as inline code instead of literal backtick characters.
    if (correct) {
      explanationEl.innerHTML = `✓ Correct. ${_inlineMarkdown(question.explanation || "")}`;
    } else {
      const correctText = question.options[question.answer];
      explanationEl.innerHTML = `✗ Correct answer: "${_inlineMarkdown(correctText)}". ${_inlineMarkdown(question.explanation || "")}`;
    }
  });

  // Lock radio inputs so the score cannot be gamed by re-submitting
  document.querySelectorAll('.answer-options input[type="radio"]').forEach(r => { r.disabled = true; });

  els.testResult.textContent = `Score: ${score}/${questions.length}`;
  setRetakeButtonsVisible(true);
  setPracticeCheckButtonsEnabled(false);
  markTestScore(selectedTopicId, score, questions.length, questions);
  renderTopicList();
}

function resetPracticeTest() {
  if (!selectedTopicId) return;
  resetPracticeProgress(selectedTopicId);
  renderPracticeTest(selectedTopicId);
  renderTopicList();
  setPracticeCheckButtonsEnabled(true);
  els.testResult.textContent = "Practice test reset. Choose answers and check again.";
}

function selectExercise(exerciseId) {
  selectedExercise = exercises.find((exercise) => exercise.id === exerciseId);
  if (!selectedExercise) return;

  els.exerciseSelect.value = exerciseId;
  els.exerciseTitle.textContent = selectedExercise.title;
  // _inlineMarkdown escapes HTML and renders `code` so backticks in the prompt
  // show as inline code instead of literal backtick characters.
  els.exercisePrompt.innerHTML = _inlineMarkdown(selectedExercise.prompt || "");

  // Load draft or starter code
  const draft = loadDraft(exerciseId);
  els.editor.value = draft || selectedExercise.starter;

  els.testOutput.textContent = "No test run yet. Press Run Tests or Ctrl+Enter.";
  // Invalidate any in-flight AI Coach stream so a late response for the
  // previous exercise cannot be written into this exercise's transcript.
  coachStreamGen++;
  _stopTypingTimer("coach");
  coachMessages = [
    {
      role: "assistant",
      text: "I can help you understand the lesson, review your code, explain test failures, or connect this topic to real-world work.",
    },
  ];
  renderCoachMessages();
  els.coachInput.value = "";
  setCoachStatus("Provider ready");
  setAskAiStatus("Provider ready");
  lastRunResult = null;
  solutionRevealed = false;
  failedAttempts = 0;

  // Show/hide solution button
  if (els.solutionBtn) {
    els.solutionBtn.style.display = selectedExercise.solution ? "" : "none";
    els.solutionBtn.textContent = "Show Solution";
  }
}

// ---------------------------------------------------------------------------
// Code execution
// ---------------------------------------------------------------------------

async function runCode() {
  if (!selectedExercise) return;
  els.testOutput.textContent = "Running local tests...";
  els.runBtn.disabled = true;
  els.runBtn.textContent = "Running...";

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        exercise_id: selectedExercise.id,
        code: els.editor.value,
      }),
    });
    const result = await response.json();
    lastRunResult = result;
    els.testOutput.innerHTML = formatResult(result);

    if (result.ok) {
      markExercisePassed(selectedExercise.id);
      renderTopicList();
      // Update only the checkmark on this option — avoids selectExercise() resetting testOutput
      const option = els.exerciseSelect.querySelector(`option[value="${selectedExercise.id}"]`);
      if (option && !option.textContent.startsWith("✓ ")) {
        option.textContent = "✓ " + option.textContent;
      }
    } else {
      failedAttempts++;
    }
  } catch (error) {
    els.testOutput.textContent = `Could not reach the local runner: ${error}`;
  } finally {
    els.runBtn.disabled = false;
    els.runBtn.textContent = "▶ Run Tests";
  }
}

// ---------------------------------------------------------------------------
// AI Coach
// ---------------------------------------------------------------------------

function setCoachStatus(text) {
  if (els.coachStatus) els.coachStatus.textContent = text;
}

function setAskAiStatus(text) {
  if (els.askAiStatus) els.askAiStatus.textContent = text;
  if (els.askAiLauncherStatus) els.askAiLauncherStatus.textContent = text;
}

function openAskAiPanel({ focusInput = false } = {}) {
  if (!els.askAiPanel || !els.askAiLauncher) return;
  els.askAiPanel.hidden = false;
  els.askAiDock?.classList.add("is-open");
  els.askAiLauncher.setAttribute("aria-expanded", "true");
  if (focusInput) {
    requestAnimationFrame(() => {
      els.askAiInput.focus();
      els.askAiInput.selectionStart = els.askAiInput.selectionEnd = els.askAiInput.value.length;
    });
  }
}

function closeAskAiPanel() {
  if (!els.askAiPanel || !els.askAiLauncher) return;
  els.askAiPanel.hidden = true;
  els.askAiDock?.classList.remove("is-open");
  els.askAiLauncher.setAttribute("aria-expanded", "false");
  els.askAiLauncher.focus();
}

/** Toggle the maximized (larger) size of the Ask AI panel. */
function toggleAskAiMaximize() {
  if (!els.askAiPanel) return;
  const maxed = els.askAiPanel.classList.toggle("maximized");
  if (els.askAiMaximize) {
    els.askAiMaximize.setAttribute("aria-pressed", String(maxed));
    els.askAiMaximize.title = maxed ? "Restore" : "Maximize";
    els.askAiMaximize.setAttribute("aria-label", maxed ? "Restore Ask AI" : "Maximize Ask AI");
  }
  // Keep the latest message in view after the size change.
  requestAnimationFrame(() => {
    if (els.askAiOutput) els.askAiOutput.scrollTop = els.askAiOutput.scrollHeight;
  });
}

function _askAiSessionTitle(messages) {
  const firstUser = messages.find((message) => message.role === "user");
  if (!firstUser) return "New chat";
  const text = firstUser.text.replace(/\s+/g, " ").trim();
  return text.length > 28 ? `${text.slice(0, 28)}…` : text;
}

function _archiveActiveAskAiSession() {
  const session = askAiSessions.find((s) => s.id === activeAskAiSessionId);
  if (session) session.title = _askAiSessionTitle(session.messages);
}

function renderAskAiSessionTabs() {
  if (!els.askAiSessionTabs) return;
  if (askAiSessions.length < 2) {
    els.askAiSessionTabs.hidden = true;
    els.askAiSessionTabs.innerHTML = "";
    return;
  }
  els.askAiSessionTabs.hidden = false;
  els.askAiSessionTabs.innerHTML = askAiSessions
    .map((session) => {
      const active = session.id === activeAskAiSessionId;
      const label = escapeHtml(session.title || "New chat");
      return `<button type="button" class="ask-ai-session-tab${active ? " active" : ""}" role="tab" aria-selected="${active}" data-session-id="${session.id}" title="${label}"><span class="ask-ai-session-tab-label">${label}</span><span class="ask-ai-session-tab-close" data-close-session-id="${session.id}" aria-label="Close chat" title="Close chat">&times;</span></button>`;
    })
    .join("");
}

function switchAskAiSession(id) {
  if (id === activeAskAiSessionId) return;
  const session = askAiSessions.find((s) => s.id === id);
  if (!session) return;
  // Invalidate any in-flight stream tied to the session we're leaving so a
  // late chunk cannot land in the chat we are switching to.
  askAiStreamGen++;
  _stopTypingTimer("askAi");
  _archiveActiveAskAiSession();
  activeAskAiSessionId = id;
  askAiMessages = session.messages;
  if (els.askAiInput) els.askAiInput.value = "";
  renderAskAiMessages();
  renderAskAiSessionTabs();
  openAskAiPanel({ focusInput: true });
  if (els.askAiOutput) requestAnimationFrame(() => { els.askAiOutput.scrollTop = 0; });
}

function closeAskAiSession(id) {
  // Always keep at least one chat open.
  if (askAiSessions.length <= 1) return;
  const idx = askAiSessions.findIndex((s) => s.id === id);
  if (idx === -1) return;
  const wasActive = id === activeAskAiSessionId;
  askAiSessions.splice(idx, 1);
  if (wasActive) {
    askAiStreamGen++;
    _stopTypingTimer("askAi");
    const next = askAiSessions[Math.max(0, idx - 1)];
    activeAskAiSessionId = next.id;
    askAiMessages = next.messages;
    renderAskAiMessages();
  }
  renderAskAiSessionTabs();
}

function startNewAskAiChat() {
  // Invalidate any in-flight Ask AI stream so a late response for the
  // previous chat cannot be written into the new chat's transcript.
  askAiStreamGen++;
  _stopTypingTimer("askAi");
  _archiveActiveAskAiSession();
  askAiSessionSeq++;
  askAiMessages = [{ role: "assistant", text: ASK_AI_WELCOME_MESSAGE }];
  askAiSessions.push({ id: askAiSessionSeq, title: "New chat", messages: askAiMessages });
  activeAskAiSessionId = askAiSessionSeq;
  if (els.askAiInput) els.askAiInput.value = "";
  setAskAiStatus("✨ New chat started");
  renderAskAiMessages();
  renderAskAiSessionTabs();
  openAskAiPanel({ focusInput: true });
  // Make the reset obvious: jump to the top of the fresh transcript, then settle
  // the status line back to the provider state after a moment.
  if (els.askAiOutput) requestAnimationFrame(() => { els.askAiOutput.scrollTop = 0; });
  setTimeout(() => setAskAiStatus("Provider ready"), 2000);
}

function isLocalAiProvider(provider = els.provider.value) {
  return LOCAL_AI_PROVIDERS.has(provider);
}

function _localProviderWarmupHint() {
  return isLocalAiProvider()
    ? " Local models sometimes need one warm-up request after launch; if this was the first question, try once more."
    : "";
}

async function askLabCoach(questionOverride = "", { skipAutoRun = false, mode = "" } = {}) {
  const generation = ++coachStreamGen;
  const question = questionOverride || els.coachInput.value.trim() || "Please review my current code and test result. Explain what I should learn next.";
  const requestMode = mode || (questionOverride ? "lab" : "chat");
  const coachHistory = coachMessages.filter((message) => message.text !== "thinking").slice(-8);
  appendCoachMessage("user", question);
  els.coachInput.value = "";
  setCoachStatus(`${els.provider.value} / ${els.model.value || "no model selected"}`);
  els.aiBtn.disabled = true;
  els.explainBtn.disabled = true;

  let runResult = lastRunResult;
  if (!runResult && selectedExercise && !skipAutoRun && questionOverride) {
    els.testOutput.textContent = "Running local tests before coach review...";
    runResult = await postJsonWithTimeout("/api/run", {
      exercise_id: selectedExercise.id,
      code: els.editor.value,
    });
    lastRunResult = runResult;
    els.testOutput.innerHTML = formatResult(runResult);
  }

  let streamIndex = null;
  try {
    appendCoachMessage("assistant", "thinking");
    const payload = {
      provider: els.provider.value,
      model: els.model.value,
      endpoint: els.endpoint.value,
      api_key: els.apiKey.value,
      topic_id: selectedTopicId,
      exercise_id: selectedExercise ? selectedExercise.id : "",
      code: selectedExercise ? els.editor.value : "",
      run_result: runResult || {},
      question,
      mode: requestMode,
      chat_history: coachHistory,
    };
    const result = await postAiStreamWithTimeout(payload, {
      onChunk: (text) => {
        if (generation !== coachStreamGen) return;
        if (streamIndex === null) {
          streamIndex = _beginStreamingAssistantMessage(coachMessages, "coach", renderCoachMessages);
          setCoachStatus("Coach is typing...");
        }
        _updateStreamingAssistantMessage(coachMessages, streamIndex, text, null, true, renderCoachMessages);
      },
    }, AI_REQUEST_TIMEOUT_MS);
    if (generation !== coachStreamGen) return;
    const prefix = result.ok ? "" : `⚠ AI Coach unavailable (${result.error}). Built-in feedback:\n\n`;
    const stats = result.ok ? {
      model: els.model.value,
      provider: els.provider.value,
      tokens_in: result.tokens_in || 0,
      tokens_out: result.tokens_out || 0,
      elapsed_sec: result.elapsed_sec || 0,
      tok_per_sec: result.tok_per_sec || 0,
    } : null;
    if (streamIndex !== null) {
      _updateStreamingAssistantMessage(
        coachMessages,
        streamIndex,
        `${prefix}${result.answer || result.error || "No response."}`,
        stats,
        false,
        renderCoachMessages
      );
    } else {
      replaceLastThinkingMessage(`${prefix}${result.answer || result.error || "No response."}`, stats);
    }
    setCoachStatus(result.ok ? "Coach response received" : "Fallback feedback shown");
  } catch (error) {
    if (generation !== coachStreamGen) return;
    const message = String(error).includes("timed out")
      ? `AI Coach request timed out. Check provider endpoint/model and try again.${_localProviderWarmupHint()}`
      : `Could not reach the AI coach route: ${error}`;
    if (streamIndex !== null) {
      _updateStreamingAssistantMessage(coachMessages, streamIndex, message, null, false, renderCoachMessages);
    } else {
      replaceLastThinkingMessage(message);
    }
    setCoachStatus("Coach unavailable");
  } finally {
    els.aiBtn.disabled = false;
    els.explainBtn.disabled = false;
  }
}

async function askFloatingAi(questionOverride = "", { includeTopicContext = false, includeHistory = !includeTopicContext } = {}) {
  const generation = ++askAiStreamGen;
  const question = questionOverride || els.askAiInput.value.trim() || "Help me understand what I am looking at on this page.";
  const contextKind = includeTopicContext ? "contextual" : "freeform";
  const askAiHistory = includeHistory
    ? askAiMessages
      .filter((message) => message.text !== "thinking" && message.contextKind !== "contextual")
      .slice(-8)
    : [];
  openAskAiPanel();
  appendAskAiMessage("user", question, { contextKind });
  els.askAiInput.value = "";
  setAskAiStatus(`${els.provider.value} / ${els.model.value || "no model selected"}`);
  els.askAiSendBtn.disabled = true;

  let streamIndex = null;
  try {
    appendAskAiMessage("assistant", "thinking", { contextKind });
    const payload = {
      provider: els.provider.value,
      model: els.model.value,
      endpoint: els.endpoint.value,
      api_key: els.apiKey.value,
      topic_id: includeTopicContext ? selectedTopicId : "",
      exercise_id: "",
      code: "",
      run_result: {},
      question,
      mode: "chat",
      chat_history: askAiHistory,
    };
    const result = await postAiStreamWithTimeout(payload, {
      onChunk: (text) => {
        if (generation !== askAiStreamGen) return;
        if (streamIndex === null) {
          streamIndex = _beginStreamingAssistantMessage(askAiMessages, "askAi", renderAskAiMessages, { contextKind });
          setAskAiStatus("Ask AI is typing...");
        }
        _updateStreamingAssistantMessage(askAiMessages, streamIndex, text, null, true, renderAskAiMessages);
      },
    }, AI_REQUEST_TIMEOUT_MS);
    if (generation !== askAiStreamGen) return;
    const prefix = result.ok ? "" : `⚠ Ask AI unavailable (${result.error}).\n\n`;
    const stats = result.ok ? {
      model: els.model.value,
      provider: els.provider.value,
      tokens_in: result.tokens_in || 0,
      tokens_out: result.tokens_out || 0,
      elapsed_sec: result.elapsed_sec || 0,
      tok_per_sec: result.tok_per_sec || 0,
    } : null;
    if (streamIndex !== null) {
      _updateStreamingAssistantMessage(
        askAiMessages,
        streamIndex,
        `${prefix}${result.answer || result.error || "No response."}`,
        stats,
        false,
        renderAskAiMessages
      );
    } else {
      replaceLastAskAiThinkingMessage(`${prefix}${result.answer || result.error || "No response."}`, stats);
    }
    setAskAiStatus(result.ok ? "Response received" : "Provider unavailable");
  } catch (error) {
    if (generation !== askAiStreamGen) return;
    const message = String(error).includes("timed out")
      ? `Ask AI request timed out. Check provider endpoint/model and try again.${_localProviderWarmupHint()}`
      : `Could not reach the AI coach route: ${error}`;
    if (streamIndex !== null) {
      _updateStreamingAssistantMessage(askAiMessages, streamIndex, message, null, false, renderAskAiMessages);
    } else {
      replaceLastAskAiThinkingMessage(message);
    }
    setAskAiStatus("Unavailable");
  } finally {
    els.askAiSendBtn.disabled = false;
  }
}

// ---------------------------------------------------------------------------
// AI settings
// ---------------------------------------------------------------------------

function saveAiSettings() {
  localStorage.setItem(
    "pySkillLabSettings",
    JSON.stringify({
      provider: els.provider.value,
      model: els.model.value,
      endpoint: els.endpoint.value,
    })
  );
}

function currentAiSettingsPayload({ includeKey = false } = {}) {
  const payload = {
    provider: els.provider.value,
    model: els.model.value,
    endpoint: els.endpoint.value,
  };
  if (includeKey) {
    payload.api_key = els.apiKey.value.trim();
  }
  return payload;
}

async function saveAiSettingsToServer({ includeKey = false, timeoutMs = 5000 } = {}) {
  const result = await postJsonWithTimeout(
    "/api/ai-settings",
    currentAiSettingsPayload({ includeKey }),
    timeoutMs
  );
  if (result.ok) {
    aiSettingsKeyPresent = !!result.key_present;
    updateAiSettingsMode();
  }
  return result;
}

function loadAiSettings() {
  // Try new key, fall back to old key for backwards compatibility
  const saved = localStorage.getItem("pySkillLabSettings") || localStorage.getItem("pyInterviewAiSettings");
  if (!saved) return;
  try {
    const settings = JSON.parse(saved);
    if (settings.provider) els.provider.value = settings.provider;
    if (settings.model) { preferredModel = settings.model; els.model.value = settings.model; }
    if (settings.endpoint) els.endpoint.value = settings.endpoint;
    // Sanitize: if old builds stored api_key, re-save without it
    if (settings.api_key !== undefined) {
      localStorage.setItem("pySkillLabSettings", JSON.stringify({
        provider: settings.provider,
        model: settings.model,
        endpoint: settings.endpoint,
      }));
    }
    localStorage.removeItem("pyInterviewAiSettings");
  } catch {
    localStorage.removeItem("pySkillLabSettings");
    localStorage.removeItem("pyInterviewAiSettings");
  }
}

async function loadServerAiSettings() {
  try {
    const response = await fetch("/api/ai-settings", { cache: "no-store" });
    const settings = await response.json();
    if (!settings.ok) return false;
    if (settings.provider) els.provider.value = settings.provider;
    if (settings.model) {
      preferredModel = settings.model;
      els.model.value = settings.model;
    }
    if (settings.endpoint) els.endpoint.value = settings.endpoint;
    aiSettingsKeyPresent = !!settings.key_present;
    els.apiKey.value = "";
    saveAiSettings();
    updateAiSettingsMode();
    _updateSettingsBtnLabel();
    await loadModels({ notify: false });
    return true;
  } catch {
    return false;
  }
}

// Default/fallback model IDs age quickly. Used as starter suggestions when a
// provider has no saved model and when a live /models refresh isn't available;
// the live refresh result is always the source of truth.
const FALLBACK_MODELS = {
  openai:    ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini"],
  anthropic: ["claude-3-5-haiku-latest", "claude-3-5-sonnet-latest"],
  google:    ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash"],
  grok:      ["grok-3-mini", "grok-3", "grok-2-1212"],
  groq:      ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"],
};

function applyProviderDefaults() {
  const defaults = {
    ollama:         { model: "",                          endpoint: "http://127.0.0.1:11434" },
    lmstudio:       { model: "",                          endpoint: "http://127.0.0.1:1234" },
    openai:         { model: "",  endpoint: "https://api.openai.com/v1/chat/completions" },
    anthropic:      { model: "",  endpoint: "https://api.anthropic.com/v1/messages" },
    google:         { model: "",  endpoint: "https://generativelanguage.googleapis.com/v1beta" },
    grok:           { model: "",  endpoint: "https://api.x.ai/v1/chat/completions" },
    groq:           { model: "",  endpoint: "https://api.groq.com/openai/v1/chat/completions" },
    "azure-foundry": { model: "",                          endpoint: "" },
  };
  const selected = defaults[els.provider.value];
  preferredModel = selected.model;
  els.model.value = selected.model;
  if (els.modelSelect) {
    els.modelSelect.innerHTML = "";
    els.modelSelect.value = "";
  }
  els.endpoint.value = selected.endpoint;
  els.apiKey.value = "";
  aiSettingsKeyPresent = false;
  updateAiSettingsMode();
  clearAiSettingsStatus();
  loadModels();
}

function clearAiSettingsStatus() {
  const statusEl = document.querySelector("#aiSettingsTestStatus");
  if (!statusEl) return;
  statusEl.hidden = true;
  statusEl.textContent = "";
  statusEl.className = "ai-settings-test-status";
}

function setAiSettingsStatus(kind, headline, detail = "") {
  const statusEl = document.querySelector("#aiSettingsTestStatus");
  if (!statusEl) return;
  statusEl.hidden = false;
  statusEl.className = `ai-settings-test-status ${kind || ""}`.trim();
  statusEl.innerHTML = [
    `<strong>${escapeHtml(headline)}</strong>`,
    detail ? `<span>${escapeHtml(detail)}</span>` : "",
  ].join("");
  requestAnimationFrame(_reclampPanel);
}

function updateAiSettingsMode() {
  const local = isLocalAiProvider();
  if (els.model && els.modelSelect) {
    els.model.hidden = local;
    els.modelSelect.hidden = !local;
  }
  if (els.refreshModelsBtn) {
    els.refreshModelsBtn.hidden = !local;
    els.refreshModelsBtn.textContent = local ? "Show local models" : "Load model list";
    els.refreshModelsBtn.title = local
      ? "Show models installed in your local provider"
      : "Load verified models from this provider";
  }
  if (els.modelHelpText) {
    els.modelHelpText.textContent = local
      ? "Use Show local models to list what is installed, choose a model, then test it."
      : "Use the recommended default or type the model name your API account can use.";
  }
  if (els.apiKeyFieldLabel) {
    els.apiKeyFieldLabel.hidden = local;
  }
  if (els.apiKeyHelpText) {
    els.apiKeyHelpText.textContent = local
      ? "Not needed for Ollama or LM Studio."
      : aiSettingsKeyPresent
        ? "Saved server-side key is available. Leave blank to keep it, or paste a new key to replace it."
        : "Saved to .env on disk when you use Save & Apply or Verify provider.";
  }
  if (els.apiKey) {
    els.apiKey.placeholder = local
      ? ""
      : aiSettingsKeyPresent
        ? "Saved key will be used"
        : "Paste API key for hosted providers";
  }
  const testBtn = document.querySelector("#aiSettingsTestBtn");
  if (testBtn) {
    testBtn.textContent = local ? "Test selected model" : "Verify provider";
  }
}

async function loadModels(options = {}) {
  const persistOnSuccess = options.persistOnSuccess === true;
  const notify = options.notify !== false;
  // Suggestions shown before a hosted API key is configured or when refresh
  // fails. Prefer live /models responses whenever available.
  const fallback = FALLBACK_MODELS[els.provider.value] || [];
  const isLocalProvider = isLocalAiProvider();
  // Capture once as a local const before any setModelOptions call.
  // setModelOptions writes back to preferredModel (module-level), so using a local const
  // means the post-fetch liveSelected calculation always sees the value from this moment.
  const currentModel = els.model.value.trim() || preferredModel;
  preferredModel = currentModel;
  setModelOptions(fallback, isLocalProvider ? (currentModel || fallback[0]) : currentModel);

  try {
    els.refreshModelsBtn.disabled = true;
    const result = await postJsonWithTimeout("/api/ai-models", {
      provider: els.provider.value,
      endpoint: els.endpoint.value,
      api_key: els.apiKey.value,
    }, 10000);
    const liveModels = result.models && result.models.length ? result.models : [];
    const models = result.ok ? (liveModels.length ? liveModels : fallback) : fallback;
    if (isLocalProvider && (!result.ok || !liveModels.length)) {
      const error = result.error || "No local models were reported by the provider.";
      setModelOptions([], "");
      _updateSettingsBtnLabel();
      setCoachStatus(`${els.provider.value} / no live model selected`);
      setAskAiStatus(`${els.provider.value} / no live model selected`);
      if (notify) {
        setAiSettingsStatus("error", "No local models found", `${error} Open the provider and install or load a model first.`);
      }
      return { ok: false, error };
    }
    // Re-read the field NOW — the user may have typed while the fetch was in flight.
    // Using currentModel (captured at call-start) would overwrite anything typed during the await.
    const fieldNow = els.model.value.trim();
    const liveSelected = models.includes(fieldNow)
      ? fieldNow
      : isLocalProvider ? models[0] : (fieldNow || models[0]);
    setModelOptions(models, liveSelected);
    if (persistOnSuccess && result.ok && models.length && !result.suggestions_only) {
      saveAiSettings();
    }
    _updateSettingsBtnLabel();
    if (result.suggestions_only) {
      setCoachStatus(`${els.provider.value} / suggested models — no API key set`);
      setAskAiStatus(`${els.provider.value} / suggested models — no API key set`);
      if (notify) {
        setAiSettingsStatus("warn", "API key required", "Showing suggested model names only. Enter a key to verify this provider.");
      }
    } else {
      setCoachStatus(`${els.provider.value} / ${els.model.value || "no live model selected"}`);
      setAskAiStatus(`${els.provider.value} / ${els.model.value || "no live model selected"}`);
      if (notify) {
        const count = result.models ? result.models.length : 0;
        const headline = isLocalProvider
          ? `${count} local model${count !== 1 ? "s" : ""} found`
          : "Model list refreshed";
        const detail = isLocalProvider
          ? "Choose the model you want to use, then run Test selected model."
          : "Choose or type the model your API account can use, then run Verify provider.";
        setAiSettingsStatus("ok", headline, detail);
      }
    }
    if (!result.ok && result.error && !result.suggestions_only) {
      const suffix = isLocalProvider
        ? "No local fallback models were shown because local providers must reflect installed models."
        : "Using fallback model list.";
      if (notify) setAiSettingsStatus("error", "Could not refresh models", `${result.error} ${suffix}`);
    } else if (result.suggestions_only && notify) {
      setAiSettingsStatus("warn", "API key required", "Showing suggested model names only. Enter your key and use Verify provider.");
    }
    return { ok: true, suggestionsOnly: !!result.suggestions_only };
  } catch (error) {
    const catchFieldNow = els.model.value.trim();
    setModelOptions(fallback, isLocalProvider ? (catchFieldNow || fallback[0]) : (catchFieldNow || fallback[0]));
    _updateSettingsBtnLabel();
    setCoachStatus(`${els.provider.value} / ${els.model.value || "no live model selected"}`);
    setAskAiStatus(`${els.provider.value} / ${els.model.value || "no live model selected"}`);
    const suffix = isLocalProvider
      ? "No local fallback models were shown because local providers must reflect installed models."
      : "Using fallback model list.";
    if (notify) setAiSettingsStatus("error", "Could not refresh models", `${error} ${suffix}`);
    return { ok: !isLocalProvider, error: String(error) };
  } finally {
    els.refreshModelsBtn.disabled = false;
  }
}

function setModelOptions(models, selectedModel) {
  const uniqueModels = [...new Set(models.filter(Boolean))];
  document.querySelector("#modelSuggestions").innerHTML = uniqueModels
    .map((m) => `<option value="${escapeHtml(m)}">`)
    .join("");
  if (els.modelSelect) {
    els.modelSelect.innerHTML = uniqueModels
      .map((m) => `<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`)
      .join("");
  }
  if (uniqueModels.length > 0) {
    // In-list → use it. Non-empty but not in list → keep it (user typed it).
    // Empty → auto-select first (local providers; first-time API provider setup).
    els.model.value = uniqueModels.includes(selectedModel) ? selectedModel : (selectedModel || uniqueModels[0]);
    if (els.modelSelect) els.modelSelect.value = els.model.value;
  } else if (selectedModel != null) {
    // Preserve a non-null selectedModel even when the list is empty (e.g. no-key state)
    els.model.value = selectedModel;
    if (els.modelSelect) els.modelSelect.innerHTML = "";
  } else {
    // No models and no preferred model — clear rather than keep a stale value
    // left over from a previously selected provider.
    els.model.value = "";
    if (els.modelSelect) els.modelSelect.innerHTML = "";
  }
  preferredModel = els.model.value;
}

// ---------------------------------------------------------------------------
// Solution reveal
// ---------------------------------------------------------------------------

function toggleSolution() {
  if (!selectedExercise || !selectedExercise.solution) return;

  if (solutionRevealed) {
    // Hide solution, restore code
    const draft = loadDraft(selectedExercise.id);
    els.editor.value = draft || selectedExercise.starter;
    els.solutionBtn.textContent = "Show Solution";
    solutionRevealed = false;
  } else {
    if (failedAttempts < 2) {
      const remaining = 2 - failedAttempts;
      const orig = els.solutionBtn.textContent;
      els.solutionBtn.textContent = `Try ${remaining} more time${remaining === 1 ? "" : "s"} first`;
      els.solutionBtn.disabled = true;
      setTimeout(() => {
        els.solutionBtn.textContent = orig;
        els.solutionBtn.disabled = false;
      }, 2500);
      return;
    }
    // Save current code as draft before showing solution
    saveDraft(selectedExercise.id, els.editor.value);
    els.editor.value = selectedExercise.solution;
    els.solutionBtn.textContent = "Hide Solution";
    solutionRevealed = true;

    if (selectedExercise.explanation) {
      appendCoachMessage("assistant", `📝 Solution explanation:\n\n${selectedExercise.explanation}`);
    }
  }
}

// ---------------------------------------------------------------------------
// Formatting
// ---------------------------------------------------------------------------

function formatResult(result) {
  const lines = [];
  if (result.stdout) {
    lines.push("Output:");
    lines.push(escapeHtml(result.stdout));
    lines.push("");
  }
  if (result.stderr) {
    lines.push('<span class="fail">Error:</span>');
    lines.push(escapeHtml(result.stderr));
    lines.push("");
  }

  if (result.tests && result.tests.length) {
    const passed = result.tests.filter((t) => t.passed).length;
    const total = result.tests.length;
    lines.push(`Tests: <span class="${passed === total ? 'pass' : 'fail'}">${passed}/${total} passed</span>`);
    if (result.tests.some((test) => test.call)) {
      lines.push("The tests called your code with these sample values:");
    }
    result.tests.forEach((test) => {
      const status = test.passed ? "PASS" : "FAIL";
      const klass = test.passed ? "pass" : "fail";
      const label = String(test.label || "");
      const call = String(test.call || "");
      const testName = call || label;
      const prefix = call && label && call !== label
        ? `${escapeHtml(label)} | ${escapeHtml(call)} returned `
        : `${escapeHtml(testName)}${testName ? " returned " : "Returned "}`;
      lines.push(
        `  <span class="${klass}">${status}</span> ${prefix}${escapeHtml(
          pyStringify(test.actual)
        )} (expected ${escapeHtml(pyStringify(test.expected))})`
      );
    });
    lines.push("");
  }

  if (result.feedback && result.feedback.length) {
    lines.push("Coach:");
    result.feedback.forEach((item) => lines.push(`  💡 ${escapeHtml(item)}`));
  }

  return lines.join("\n");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

// Like JSON.stringify, but renders None instead of null so Python return
// values read the way a learner typed them, not as JS's "null".
function pyStringify(value) {
  if (value === null) return "None";
  if (Array.isArray(value)) return `[${value.map(pyStringify).join(", ")}]`;
  if (typeof value === "object") {
    return `{${Object.entries(value).map(([k, v]) => `${JSON.stringify(k)}: ${pyStringify(v)}`).join(", ")}}`;
  }
  return JSON.stringify(value);
}

function isRunnableSnippet(code, lang) {
  if (!lang || !lang.includes('run')) return false;
  const baseLang = lang.split(/\s+/)[0];
  if (baseLang !== 'python') return false;
  const blocked = /\b(?:import|from)\s+(?:os|sys|subprocess|shutil|socket|pathlib|urllib|http|ctypes|signal|multiprocessing|threading|pickle|importlib|runpy)\b/;
  const thirdParty = /\b(?:import|from)\s+(?:fastapi|pydantic|langchain|langgraph|mcp|uvicorn|anthropic|openai|numpy|pandas|aiohttp|httpx|starlette|sqlalchemy)\b/;
  const banned = /\binput\s*\(|\bopen\s*\(/;
  return !blocked.test(code) && !thirdParty.test(code) && !banned.test(code);
}

/** Markdown renderer for lesson section bodies — supports paragraphs, code blocks, inline code, bold. */
function renderLessonMarkdown(text) {
  if (!text) return '';
  const segments = [];
  const codeBlockRe = /```([^\n`]*)\n([\s\S]*?)```/g;
  let lastIdx = 0;
  let m;
  while ((m = codeBlockRe.exec(text)) !== null) {
    if (m.index > lastIdx) segments.push({ type: 'text', content: text.slice(lastIdx, m.index) });
    segments.push({ type: 'code', content: m[2].replace(/^\n/, '').replace(/\n$/, ''), lang: (m[1] || '').trim() });
    lastIdx = m.index + m[0].length;
  }
  if (lastIdx < text.length) segments.push({ type: 'text', content: text.slice(lastIdx) });
  if (!segments.length) segments.push({ type: 'text', content: text });

  function inlineMarkdown(raw) {
    let result = '';
    let remaining = raw;
    while (remaining.length > 0) {
      const btIdx = remaining.indexOf('`');
      const boldIdx = remaining.indexOf('**');
      let nextIdx = -1, nextType = null;
      if (btIdx !== -1 && (boldIdx === -1 || btIdx < boldIdx)) { nextIdx = btIdx; nextType = 'code'; }
      else if (boldIdx !== -1) { nextIdx = boldIdx; nextType = 'bold'; }
      if (nextIdx === -1) { result += escapeHtml(remaining); break; }
      result += escapeHtml(remaining.slice(0, nextIdx));
      remaining = remaining.slice(nextIdx);
      if (nextType === 'code') {
        const end = remaining.indexOf('`', 1);
        if (end !== -1) { result += `<code class="inline-code">${escapeHtml(remaining.slice(1, end))}</code>`; remaining = remaining.slice(end + 1); }
        else { result += escapeHtml(remaining[0]); remaining = remaining.slice(1); }
      } else {
        const end = remaining.indexOf('**', 2);
        if (end !== -1) { result += `<strong>${escapeHtml(remaining.slice(2, end))}</strong>`; remaining = remaining.slice(end + 2); }
        else { result += escapeHtml(remaining.slice(0, 2)); remaining = remaining.slice(2); }
      }
    }
    return result;
  }

  let html = '';
  for (const seg of segments) {
    if (seg.type === 'code') {
      const canRun = isRunnableSnippet(seg.content, seg.lang);
      const codeAction = canRun
        ? `<button type="button" class="lesson-try-btn" data-code="${escapeHtml(seg.content)}" title="Load in scratchpad">&#9654; Try it</button>`
        : `<span class="lesson-code-note">Illustration only</span>`;
      html += `<div class="lesson-code-wrap"><pre class="lesson-code" tabindex="0"><code>${escapeHtml(seg.content)}</code></pre>${codeAction}</div>`;
    } else {
      // Block-level prose: paragraphs plus bullet/numbered lists. Without list
      // handling, `- item` lines collapse into one run-on paragraph.
      const lines = seg.content.split('\n');
      let paraLines = [];
      let i = 0;
      const flushPara = () => {
        if (paraLines.length) { html += `<p>${inlineMarkdown(paraLines.join(' ').trim())}</p>`; paraLines = []; }
      };
      while (i < lines.length) {
        const t = lines[i].trim();
        if (!t) { flushPara(); i++; continue; }
        if (/^[-*+]\s+/.test(t)) {
          flushPara();
          html += '<ul class="lesson-list">';
          while (i < lines.length && /^[-*+]\s+/.test(lines[i].trim())) {
            html += `<li>${inlineMarkdown(lines[i].trim().replace(/^[-*+]\s+/, ''))}</li>`;
            i++;
          }
          html += '</ul>';
          continue;
        }
        if (/^\d+\.\s+/.test(t)) {
          flushPara();
          html += '<ol class="lesson-list">';
          while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
            html += `<li>${inlineMarkdown(lines[i].trim().replace(/^\d+\.\s+/, ''))}</li>`;
            i++;
          }
          html += '</ol>';
          continue;
        }
        paraLines.push(t);
        i++;
      }
      flushPara();
    }
  }
  return html || `<p>${escapeHtml(text)}</p>`;
}

/** Simple markdown-like rendering for coach messages. */
/**
 * Strip reasoning-model thinking from chat text. The server already filters
 * <think>...</think>, but this is defense-in-depth so raw reasoning can never
 * leak into the transcript even if a provider/path slips one through.
 */
function stripThinkTags(text) {
  return String(text || "")
    .replace(/<think>[\s\S]*?<\/think>/gi, "")
    // An unclosed <think> (reasoning still streaming, or no closing tag at all)
    // — hide everything from the tag onward rather than showing the reasoning.
    .replace(/<think>[\s\S]*$/i, "");
}

/** Inline markdown for one line/paragraph: `code`, **bold**, *italic*. */
function _inlineMarkdown(raw) {
  let result = "";
  let remaining = raw;
  while (remaining.length > 0) {
    const btIdx = remaining.indexOf("`");
    const boldIdx = remaining.indexOf("**");
    let itIdx = -1;
    for (let i = 0; i < remaining.length; i++) {
      if (remaining[i] === "*" && remaining[i + 1] !== "*" && remaining[i - 1] !== "*") { itIdx = i; break; }
    }
    const cands = [[btIdx, "code"], [boldIdx, "bold"], [itIdx, "italic"]]
      .filter((c) => c[0] !== -1)
      .sort((a, b) => a[0] - b[0]);
    if (!cands.length) { result += escapeHtml(remaining); break; }
    const [nextIdx, nextType] = cands[0];
    result += escapeHtml(remaining.slice(0, nextIdx));
    remaining = remaining.slice(nextIdx);
    if (nextType === "code") {
      const end = remaining.indexOf("`", 1);
      if (end !== -1) { result += `<code class="inline-code">${escapeHtml(remaining.slice(1, end))}</code>`; remaining = remaining.slice(end + 1); }
      else { result += escapeHtml(remaining[0]); remaining = remaining.slice(1); }
    } else if (nextType === "bold") {
      const end = remaining.indexOf("**", 2);
      if (end !== -1) { result += `<strong>${escapeHtml(remaining.slice(2, end))}</strong>`; remaining = remaining.slice(end + 2); }
      else { result += escapeHtml(remaining.slice(0, 2)); remaining = remaining.slice(2); }
    } else {
      const end = remaining.indexOf("*", 1);
      if (end !== -1) { result += `<em>${escapeHtml(remaining.slice(1, end))}</em>`; remaining = remaining.slice(end + 1); }
      else { result += escapeHtml(remaining[0]); remaining = remaining.slice(1); }
    }
  }
  return result;
}

/** Block-level markdown for chat: headings, lists, and paragraphs. */
function _renderTextBlock(content) {
  const lines = content.split("\n");
  let html = "";
  let paraLines = [];
  let i = 0;
  const flushPara = () => {
    if (paraLines.length) {
      // Join soft-wrapped lines with a space so prose does not become a stack
      // of one-fragment-per-line — the core "disoriented chat" fix.
      html += `<p>${_inlineMarkdown(paraLines.join(" ").trim())}</p>`;
      paraLines = [];
    }
  };
  while (i < lines.length) {
    const t = lines[i].trim();
    if (!t) { flushPara(); i++; continue; }
    const heading = /^(#{1,6})\s+(.*)$/.exec(t);
    if (heading) {
      flushPara();
      const level = Math.min(6, heading[1].length);
      html += `<div class="md-h md-h${level}">${_inlineMarkdown(heading[2].trim())}</div>`;
      i++;
      continue;
    }
    if (/^[-*+]\s+/.test(t)) {
      flushPara();
      html += "<ul>";
      while (i < lines.length && /^[-*+]\s+/.test(lines[i].trim())) {
        html += `<li>${_inlineMarkdown(lines[i].trim().replace(/^[-*+]\s+/, ""))}</li>`;
        i++;
      }
      html += "</ul>";
      continue;
    }
    if (/^\d+\.\s+/.test(t)) {
      flushPara();
      html += "<ol>";
      while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
        html += `<li>${_inlineMarkdown(lines[i].trim().replace(/^\d+\.\s+/, ""))}</li>`;
        i++;
      }
      html += "</ol>";
      continue;
    }
    paraLines.push(t);
    i++;
  }
  flushPara();
  return html;
}

/** Markdown renderer for chat (Coach + Ask AI). Handles code fences, headings, lists, inline. */
function renderMarkdown(text) {
  const cleaned = stripThinkTags(text);
  const segments = [];
  const codeRe = /```([^\n`]*)\n([\s\S]*?)```/g;
  let last = 0;
  let m;
  while ((m = codeRe.exec(cleaned)) !== null) {
    if (m.index > last) segments.push({ type: "text", content: cleaned.slice(last, m.index) });
    segments.push({ type: "code", content: m[2].replace(/\n$/, "") });
    last = m.index + m[0].length;
  }
  if (last < cleaned.length) segments.push({ type: "text", content: cleaned.slice(last) });

  let html = "";
  for (const seg of segments) {
    if (seg.type === "code") {
      html += `<pre class="coach-code" tabindex="0"><code>${escapeHtml(seg.content)}</code></pre>`;
    } else {
      html += _renderTextBlock(seg.content);
    }
  }
  return html;
}

// ---------------------------------------------------------------------------
// Scratchpad
// ---------------------------------------------------------------------------

function loadInScratchpad(code) {
  if (els.scratchBody.hidden) {
    els.scratchBody.hidden = false;
    els.scratchToggle.setAttribute("aria-expanded", "true");
  }
  els.scratchEditor.value = code;
  els.scratchOutput.textContent = "Ready.";
  els.scratchEditor.focus();
  els.scratchpad.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function runScratchpad() {
  const code = els.scratchEditor.value.trim();
  if (!code) return;
  els.scratchOutput.textContent = "Running…";
  els.scratchRunBtn.disabled = true;
  els.scratchRunBtn.textContent = "Running…";
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    });
    const result = await response.json();
    const parts = [];
    if (result.stdout) parts.push(result.stdout);
    if (result.stderr) parts.push(`[stderr]\n${result.stderr}`);
    if (result.error) parts.push(`[error] ${result.error}`);
    els.scratchOutput.textContent = parts.join("\n").trimEnd() || "(no output)";
  } catch (err) {
    els.scratchOutput.textContent = `Could not reach runner: ${err}`;
  } finally {
    els.scratchRunBtn.disabled = false;
    els.scratchRunBtn.textContent = "▶ Run";
  }
}

// ---------------------------------------------------------------------------
// Execution visualizer (step-through)
// ---------------------------------------------------------------------------

let vizState = {
  steps: [],
  index: -1,
  lines: [],
  stdout: "",
  notes: {},
};

let _vizReturnFocus = null;
let _codePopupReturnFocus = null;

function openVizOverlay(lines) {
  els.vizCode.innerHTML = lines
    .map((line, i) => `<span class="viz-ln" data-i="${i}">${escapeHtml(line) || " "}</span>`)
    .join("");
  els.vizOverlay.hidden = false;
  // Move keyboard focus into the modal so keyboard/screen-reader users land inside it.
  if (els.vizClose) requestAnimationFrame(() => els.vizClose.focus());
}

function visualizerBuiltInErrorNote(error) {
  const text = String(error || "");
  if (/input\(\) is not available/i.test(text)) {
    return "input() is blocked here because this runner cannot pause and wait for keyboard input. Use a sample variable or pass a value into your function instead.";
  }
  if (/open\(\) is not available/i.test(text)) {
    return "open() is blocked in this learning runner so code cannot read or write local files. Use variables, lists, dictionaries, or function parameters instead.";
  }
  if (/not allowed in the practice sandbox|not allowed in this sandbox|restricted in the sandbox/i.test(text)) {
    return "This code uses something the local learning runner blocks before execution. The block keeps practice code focused on Python logic instead of system access.";
  }
  return "";
}

async function openVisualizer(code, sourceBtn) {
  const cleaned = (code || "").replace(/\s+$/, "");
  if (!cleaned.trim()) return;
  // Remember what to focus when the visualizer closes.
  _vizReturnFocus = sourceBtn || document.activeElement;
  const label = sourceBtn ? sourceBtn.innerHTML : "";
  if (sourceBtn) {
    sourceBtn.disabled = true;
    sourceBtn.textContent = "Tracing…";
  }
  try {
    const result = await postJsonWithTimeout("/api/trace", { code: cleaned });
    vizState = {
      steps: result.steps || [],
      index: -1,
      lines: cleaned.split("\n"),
      error: result.error,
      error_line: result.error_line || 0,
      truncated: result.truncated,
      stdout: (result.stdout || "").trimEnd(),
      notes: {},
    };
    openVizOverlay(vizState.lines);
    if (!vizState.steps.length) {
      // Compile-time error (e.g. SyntaxError) — highlight the offending line
      if (vizState.error_line > 0) {
        const errEl = els.vizCode.querySelectorAll(".viz-ln")[vizState.error_line - 1];
        if (errEl) errEl.classList.add("viz-ln-error");
      }
      els.vizVarList.innerHTML = '<p class="viz-empty">Python stopped before running any code.</p>';
      els.vizPrev.disabled = true;
      els.vizNext.disabled = true;
      els.vizCount.textContent = "";
      const builtInNote = visualizerBuiltInErrorNote(vizState.error);
      // Deterministic visualizer path: AI runs only when the learner clicks Ask AI.
      els.vizNote.textContent = vizState.error
        ? `Error — ${vizState.error}`
        : "No executable steps.";
      if (builtInNote) {
        els.vizNote.textContent = builtInNote;
        vizState.notes["0"] = builtInNote;
      }
    } else {
      stepViz(1);
    }
  } catch (err) {
    openVizOverlay(cleaned.split("\n"));
    els.vizNote.textContent = `Could not reach the visualizer: ${err}`;
    els.vizPrev.disabled = true;
    els.vizNext.disabled = true;
  } finally {
    if (sourceBtn) {
      sourceBtn.disabled = false;
      sourceBtn.innerHTML = label;
    }
  }
}

function renderViz() {
  // 0-steps case: compile-time error or blocked code, no navigation.
  if (!vizState.steps.length) {
    if (vizState.notes["0"]) {
      els.vizNote.innerHTML = `<span class="viz-ai-badge">Runner</span> ${escapeHtml(vizState.notes["0"])}`;
    } else {
      els.vizNote.textContent = vizState.error
        ? `Error — ${vizState.error}`
        : "No executable steps.";
    }
    return;
  }

  const step = vizState.index >= 0 ? vizState.steps[vizState.index] : null;
  const prevStep = vizState.index > 0 ? vizState.steps[vizState.index - 1] : null;
  document.querySelectorAll(".viz-ln").forEach((el, i) => {
    el.classList.toggle("active", step && i === step.line - 1);
  });

  if (!step) {
    els.vizVarList.innerHTML = '<p class="viz-empty">Press Next to start.</p>';
    els.vizNote.innerHTML = "";
    return;
  }

  // --- Variables panel with change highlighting ---
  const names = Object.keys(step.vars || {});
  const prevVars = prevStep ? (prevStep.vars || {}) : {};
  let html = names.length
    ? names.map((n) => {
        const isNew = !(n in prevVars);
        const isChanged = !isNew && JSON.stringify(prevVars[n]) !== JSON.stringify(step.vars[n]);
        const cls = isNew ? " viz-var-new" : isChanged ? " viz-var-changed" : "";
        const badge = isNew ? '<span class="viz-var-badge">new</span>' : isChanged ? '<span class="viz-var-badge">changed</span>' : "";
        return `<div class="viz-var${cls}">${badge}<span class="viz-var-name">${escapeHtml(n)}</span><span class="viz-var-val">${escapeHtml(pyStringify(step.vars[n]))}</span></div>`;
      }).join("")
    : '<p class="viz-empty">No variables yet.</p>';

  // --- Per-step stdout (shows output as it accumulates, not just at the end) ---
  const outNow = (step.out || "").trimEnd();
  if (outNow) {
    html += `<div class="viz-output-label">Output so far</div><pre class="viz-stdout">${escapeHtml(outNow)}</pre>`;
  }
  els.vizVarList.innerHTML = html;

  // --- Note: deterministic line-number fallback. Ask AI is manual.
  if (step.final) {
    els.vizNote.textContent = vizState.error
      ? `Python stopped here with an error — ${vizState.error}.`
      : "Done — execution complete.";
  } else {
    els.vizNote.textContent = `About to run line ${step.line}.`;
  }

  els.vizPrev.disabled = vizState.index <= 0;
  const atEnd = vizState.index >= vizState.steps.length - 1;
  els.vizNext.disabled = atEnd;
  els.vizNext.textContent = atEnd ? "End" : "Next →";
  els.vizCount.textContent = `Step ${vizState.index + 1} of ${vizState.steps.length}${vizState.truncated ? " (capped)" : ""}`;
}

function stepViz(delta) {
  const next = vizState.index + delta;
  if (next < 0 || next >= vizState.steps.length) return;
  vizState.index = next;
  renderViz();
}

function closeViz() {
  els.vizOverlay.hidden = true;
  vizState = {
    steps: [],
    index: -1,
    lines: [],
    stdout: "",
    notes: {},
  };
  // Reset any position set by dragging so next open re-centers
  els.vizModal.style.transform = "";
  els.vizModal.style.top = "";
  els.vizModal.style.left = "";
  // Return focus to the control that opened the visualizer.
  if (_vizReturnFocus && typeof _vizReturnFocus.focus === "function") _vizReturnFocus.focus();
  _vizReturnFocus = null;
}

// ---------------------------------------------------------------------------
// Code try-it popup
// ---------------------------------------------------------------------------

function openCodePopup(code) {
  // Capture the trigger (e.g. the Try-it button) so focus can return on close.
  _codePopupReturnFocus = document.activeElement;
  els.codePopupEditor.value = code;
  els.codePopupOutput.textContent = "Ready.";
  els.codePopup.classList.remove("maximized");
  if (els.codePopupMaxBtn) { els.codePopupMaxBtn.textContent = "⤢"; els.codePopupMaxBtn.title = "Maximize"; }
  els.codePopup.hidden = false;
  els.codePopupEditor.focus();
}

function closeCodePopup() {
  els.codePopup.hidden = true;
  els.codePopup.classList.remove("maximized");
  els.codePopupModal.style.transform = "";
  els.codePopupModal.style.top = "";
  els.codePopupModal.style.left = "";
  if (_codePopupReturnFocus && typeof _codePopupReturnFocus.focus === "function") _codePopupReturnFocus.focus();
  _codePopupReturnFocus = null;
}

function toggleCodePopupMax() {
  const maximized = els.codePopup.classList.toggle("maximized");
  els.codePopupMaxBtn.textContent = maximized ? "⤡" : "⤢";
  els.codePopupMaxBtn.title = maximized ? "Restore" : "Maximize";
}

async function runCodePopup() {
  const code = els.codePopupEditor.value.trim();
  if (!code) return;
  els.codePopupOutput.textContent = "Running…";
  els.codePopupRunBtn.disabled = true;
  els.codePopupRunBtn.textContent = "Running…";
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    });
    const result = await response.json();
    const parts = [];
    if (result.stdout) parts.push(result.stdout);
    if (result.stderr) parts.push(`[stderr]\n${result.stderr}`);
    if (result.error) parts.push(`[error] ${result.error}`);
    els.codePopupOutput.textContent = parts.join("\n").trimEnd() || "(no output)";
  } catch (err) {
    els.codePopupOutput.textContent = `Could not reach runner: ${err}`;
  } finally {
    els.codePopupRunBtn.disabled = false;
    els.codePopupRunBtn.textContent = "▶ Run";
  }
}

// ---------------------------------------------------------------------------
// UI state
// ---------------------------------------------------------------------------

function setActiveTopicSection(sectionId) {
  document.querySelectorAll(".topic-section").forEach((section) => {
    section.classList.toggle("active", section.id === sectionId);
  });
  document.querySelectorAll(".mode-button").forEach((button) => {
    const isActive = button.dataset.section === sectionId;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
  });
}

function appendCoachMessage(role, text) {
  coachMessages.push({ role, text });
  renderCoachMessages();
}

function appendAskAiMessage(role, text, meta = {}) {
  askAiMessages.push({ role, text, ...meta });
  renderAskAiMessages();
}

function _stopTypingTimer(kind) {
  if (kind === "coach" && coachTypingTimer) {
    clearInterval(coachTypingTimer);
    coachTypingTimer = null;
  }
  if (kind === "askAi" && askAiTypingTimer) {
    clearInterval(askAiTypingTimer);
    askAiTypingTimer = null;
  }
}

function _animateAssistantMessage(messages, kind, text, stats, renderFn) {
  _stopTypingTimer(kind);
  const thinkingIndex = messages.map((message) => message.text).lastIndexOf("thinking");
  const index = thinkingIndex >= 0 ? thinkingIndex : messages.length;
  const existing = messages[index] || {};
  messages[index] = { role: "assistant", text: "", stats: null, typing: true, contextKind: existing.contextKind };
  renderFn();

  let cursor = 0;
  const timer = setInterval(() => {
    cursor = Math.min(text.length, cursor + MESSAGE_TYPE_CHUNK_SIZE);
    messages[index] = {
      role: "assistant",
      text: text.slice(0, cursor),
      stats: cursor >= text.length ? stats : null,
      typing: cursor < text.length,
      contextKind: existing.contextKind,
    };
    renderFn();
    if (cursor >= text.length) {
      clearInterval(timer);
      if (kind === "coach") coachTypingTimer = null;
      if (kind === "askAi") askAiTypingTimer = null;
    }
  }, MESSAGE_TYPE_INTERVAL_MS);

  if (kind === "coach") coachTypingTimer = timer;
  if (kind === "askAi") askAiTypingTimer = timer;
}

function _beginStreamingAssistantMessage(messages, kind, renderFn, meta = {}) {
  _stopTypingTimer(kind);
  const thinkingIndex = messages.map((message) => message.text).lastIndexOf("thinking");
  const index = thinkingIndex >= 0 ? thinkingIndex : messages.length;
  const existing = messages[index] || {};
  messages[index] = {
    role: "assistant",
    text: "",
    stats: null,
    typing: true,
    contextKind: existing.contextKind,
    ...meta,
  };
  renderFn();
  return index;
}

function _updateStreamingAssistantMessage(messages, index, text, stats, typing, renderFn) {
  const existing = messages[index] || {};
  messages[index] = {
    ...existing,
    role: "assistant",
    text,
    stats: typing ? null : stats,
    typing,
  };
  renderFn();
}

function replaceLastThinkingMessage(text, stats = null) {
  _animateAssistantMessage(coachMessages, "coach", text, stats, renderCoachMessages);
}

function replaceLastAskAiThinkingMessage(text, stats = null) {
  _animateAssistantMessage(askAiMessages, "askAi", text, stats, renderAskAiMessages);
}

function _renderMessageStats(stats) {
  if (!stats) return "";
  const parts = [];
  if (stats.model) parts.push(escapeHtml(stats.model));
  if (stats.tokens_out > 0) parts.push(`${stats.tokens_out} out`);
  if (stats.tokens_in > 0) parts.push(`${stats.tokens_in} in`);
  if (stats.tok_per_sec > 0) parts.push(`${stats.tok_per_sec} tok/s`);
  if (stats.elapsed_sec > 0) parts.push(`${stats.elapsed_sec}s`);
  if (!parts.length) return "";
  return `<div class="message-stats">${parts.join(" · ")}</div>`;
}

function renderCoachMessages() {
  els.aiOutput.innerHTML = coachMessages
    .map(
      (message) => {
        if (message.text === "thinking") {
          return `
            <div class="coach-message assistant thinking">
              <strong>Coach</strong>
              <div class="thinking-dots"><span></span><span></span><span></span></div>
            </div>
          `;
        }
        const content = message.role === "assistant" ? renderMarkdown(message.text) : escapeHtml(message.text);
        const typingClass = message.typing ? " is-typing" : "";
        const statsHtml = message.role === "assistant" && !message.typing ? _renderMessageStats(message.stats) : "";
        return `
          <div class="coach-message ${message.role}${typingClass}">
            <strong>${message.role === "user" ? "You" : "Coach"}</strong>
            <div class="message-content">${content}</div>
            ${statsHtml}
          </div>
        `;
      }
    )
    .join("");
  requestAnimationFrame(() => { els.aiOutput.scrollTop = els.aiOutput.scrollHeight; });
}

function renderAskAiMessages() {
  els.askAiOutput.innerHTML = askAiMessages
    .map(
      (message) => {
        if (message.text === "thinking") {
          return `
            <div class="coach-message assistant thinking">
              <strong>Ask AI</strong>
              <div class="thinking-dots"><span></span><span></span><span></span></div>
            </div>
          `;
        }
        const content = message.role === "assistant" ? renderMarkdown(message.text) : escapeHtml(message.text);
        const typingClass = message.typing ? " is-typing" : "";
        const statsHtml = message.role === "assistant" && !message.typing ? _renderMessageStats(message.stats) : "";
        return `
          <div class="coach-message ${message.role}${typingClass}">
            <strong>${message.role === "user" ? "You" : "Ask AI"}</strong>
            <div class="message-content">${content}</div>
            ${statsHtml}
          </div>
        `;
      }
    )
    .join("");
  requestAnimationFrame(() => { els.askAiOutput.scrollTop = els.askAiOutput.scrollHeight; });
}

// ---------------------------------------------------------------------------
// Event listeners
// ---------------------------------------------------------------------------

// Auto-grow coach input as user types/pastes
els.coachInput.addEventListener("input", function () {
  this.style.height = "auto";
  this.style.height = Math.min(this.scrollHeight, 200) + "px";
});

els.search.addEventListener("input", renderTopicList);
els.exerciseSelect.addEventListener("change", (event) => selectExercise(event.target.value));
els.runBtn.addEventListener("click", runCode);
els.aiBtn.addEventListener("click", () => askLabCoach());
els.explainBtn.addEventListener("click", () => askLabCoach("Explain my current code and test result. Give me one small next step, not the full answer unless it already passes."));
els.resetBtn.addEventListener("click", () => {
  if (selectedExercise) {
    clearDraft(selectedExercise.id);
    selectExercise(selectedExercise.id);
  }
});
els.hintBtn.addEventListener("click", () => {
  if (selectedExercise) {
    // innerHTML + _inlineMarkdown so backticks in hints render as inline code.
    els.testOutput.innerHTML = `💡 Hint: ${_inlineMarkdown(selectedExercise.hint || "")}`;
  }
});

if (els.solutionBtn) {
  els.solutionBtn.addEventListener("click", toggleSolution);
}

if (els.askAiLauncher) {
  els.askAiLauncher.addEventListener("click", () => {
    if (els.askAiPanel.hidden) openAskAiPanel({ focusInput: true });
    else closeAskAiPanel();
  });
}

if (els.askAiClose) {
  els.askAiClose.addEventListener("click", closeAskAiPanel);
}

if (els.askAiMinimize) {
  // Minimize collapses the panel back to the chat bubble, keeping the conversation.
  els.askAiMinimize.addEventListener("click", closeAskAiPanel);
}

if (els.askAiMaximize) {
  els.askAiMaximize.addEventListener("click", toggleAskAiMaximize);
}

if (els.askAiNewChat) {
  els.askAiNewChat.addEventListener("click", startNewAskAiChat);
}

if (els.askAiSessionTabs) {
  els.askAiSessionTabs.addEventListener("click", (event) => {
    const closeBtn = event.target.closest("[data-close-session-id]");
    if (closeBtn) {
      event.stopPropagation();
      closeAskAiSession(Number(closeBtn.dataset.closeSessionId));
      return;
    }
    const tab = event.target.closest("[data-session-id]");
    if (tab) switchAskAiSession(Number(tab.dataset.sessionId));
  });
}

// Code editor: Tab indent + Ctrl+Enter to run + auto-save
els.editor.addEventListener("keydown", (event) => {
  if (event.key === "Tab") {
    event.preventDefault();
    const start = els.editor.selectionStart;
    const end = els.editor.selectionEnd;
    els.editor.value = `${els.editor.value.slice(0, start)}    ${els.editor.value.slice(end)}`;
    els.editor.selectionStart = els.editor.selectionEnd = start + 4;
  }
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    runCode();
  }
  if ((event.key === "s" || event.key === "S") && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    if (selectedExercise) saveDraft(selectedExercise.id, els.editor.value);
    setCoachStatus("Draft saved");
    setTimeout(() => { setCoachStatus("Provider ready"); }, 1500);
  }
});

// Auto-save on input (debounced)
let saveTimer = null;
els.editor.addEventListener("input", () => {
  if (selectedExercise) {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => saveDraft(selectedExercise.id, els.editor.value), 1000);
  }
});

els.provider.addEventListener("change", () => {
  applyProviderDefaults();
  _updateSettingsBtnLabel();
});
els.model.addEventListener("change", () => {
  preferredModel = els.model.value;
  if (els.modelSelect && els.modelSelect.value !== els.model.value) {
    els.modelSelect.value = els.model.value;
  }
  clearAiSettingsStatus();
  updateAiSettingsMode();
  setCoachStatus("AI settings changed — click Save & Apply");
  setAskAiStatus("AI settings changed — click Save & Apply");
  _updateSettingsBtnLabel();
});
if (els.modelSelect) {
  els.modelSelect.addEventListener("change", () => {
    els.model.value = els.modelSelect.value;
    preferredModel = els.model.value;
    clearAiSettingsStatus();
    setCoachStatus("AI settings changed — click Save & Apply");
    setAskAiStatus("AI settings changed — click Save & Apply");
    _updateSettingsBtnLabel();
  });
}
els.endpoint.addEventListener("change", () => {
  setCoachStatus("AI settings changed — click Save & Apply");
  setAskAiStatus("AI settings changed — click Save & Apply");
});
els.apiKey.addEventListener("change", () => {
  if (els.apiKey.value.trim()) aiSettingsKeyPresent = false;
  updateAiSettingsMode();
  setCoachStatus("AI settings changed — click Save & Apply");
  setAskAiStatus("AI settings changed — click Save & Apply");
});
els.refreshModelsBtn.addEventListener("click", () => loadModels({ notify: true }));
document.querySelectorAll(".mode-button").forEach((button) => {
  button.addEventListener("click", () => setActiveTopicSection(button.dataset.section));
});
[els.checkTestBtn, els.checkTestBtnBottom].forEach((button) => {
  if (button) button.addEventListener("click", checkPracticeTest);
});
[els.resetTestBtn, els.resetTestBtnBottom].forEach((button) => {
  if (button) button.addEventListener("click", resetPracticeTest);
});
els.coachInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    askLabCoach();
  }
});

els.askAiInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    askFloatingAi();
  }
});

els.askAiInput.addEventListener("input", function () {
  this.style.height = "auto";
  this.style.height = Math.min(this.scrollHeight, 200) + "px";
});

els.askAiSendBtn.addEventListener("click", () => askFloatingAi());

// Scratchpad toggle
els.scratchToggle.addEventListener("click", () => {
  const expanding = els.scratchBody.hidden;
  els.scratchBody.hidden = !expanding;
  els.scratchToggle.setAttribute("aria-expanded", String(expanding));
});
els.scratchToggle.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") { e.preventDefault(); els.scratchToggle.click(); }
});

// Scratchpad editor keyboard shortcuts
els.scratchEditor.addEventListener("keydown", (e) => {
  if (e.key === "Tab") {
    e.preventDefault();
    const s = els.scratchEditor.selectionStart;
    const en = els.scratchEditor.selectionEnd;
    els.scratchEditor.value = `${els.scratchEditor.value.slice(0, s)}    ${els.scratchEditor.value.slice(en)}`;
    els.scratchEditor.selectionStart = els.scratchEditor.selectionEnd = s + 4;
  }
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    runScratchpad();
  }
});

els.scratchRunBtn.addEventListener("click", runScratchpad);
els.scratchVizBtn.addEventListener("click", () => openVisualizer(els.scratchEditor.value, els.scratchVizBtn));
els.scratchClearBtn.addEventListener("click", () => {
  els.scratchEditor.value = "";
  els.scratchOutput.textContent = "Ready.";
  els.scratchEditor.focus();
});
if (els.labVizBtn) {
  els.labVizBtn.addEventListener("click", () => openVisualizer(els.editor.value, els.labVizBtn));
}
els.vizNext.addEventListener("click", () => stepViz(1));
els.vizPrev.addEventListener("click", () => stepViz(-1));
els.vizClose.addEventListener("click", closeViz);
els.vizAskAiBtn.addEventListener("click", () => {
  const step = vizState.index >= 0 ? vizState.steps[vizState.index] : null;
  const question = step
    ? "Explain what is happening on this line. What does this code do and what do the current variable values mean for a complete beginner?"
    : vizState.error
    ? "Explain what this error means in plain words and exactly how to fix it."
    : "Explain what this code does step by step.";
  askInlineViz(question);
});
els.vizOverlay.addEventListener("click", (e) => { if (e.target === els.vizOverlay) closeViz(); });
document.addEventListener("keydown", (e) => {
  if (els.vizOverlay.hidden) return;
  if (e.key === "Escape") {
    if (els.askAiPanel && !els.askAiPanel.hidden) {
      closeAskAiPanel();
      e.preventDefault();
      e.stopImmediatePropagation();
      return;
    }
    closeViz();
    e.preventDefault();
    e.stopImmediatePropagation();
  }
  else if (e.key === "ArrowRight") stepViz(1);
  else if (e.key === "ArrowLeft") stepViz(-1);
});

// Draggable viz modal — drag by the header
els.vizModalHead.addEventListener("mousedown", (e) => {
  if (e.button !== 0) return;
  e.preventDefault();
  const rect = els.vizModal.getBoundingClientRect();
  // Freeze the modal's current position, replacing the CSS transform centering
  els.vizModal.style.transform = "none";
  els.vizModal.style.top = rect.top + "px";
  els.vizModal.style.left = rect.left + "px";
  vizDrag.active = true;
  vizDrag.startX = e.clientX - rect.left;
  vizDrag.startY = e.clientY - rect.top;
  els.vizModalHead.style.cursor = "grabbing";
});

document.addEventListener("mousemove", (e) => {
  if (vizDrag.active) {
    const maxX = window.innerWidth - els.vizModal.offsetWidth;
    const maxY = window.innerHeight - els.vizModal.offsetHeight;
    els.vizModal.style.left = Math.max(0, Math.min(maxX, e.clientX - vizDrag.startX)) + "px";
    els.vizModal.style.top = Math.max(0, Math.min(maxY, e.clientY - vizDrag.startY)) + "px";
  }
  if (codePopupDrag.active) {
    const maxX = window.innerWidth - els.codePopupModal.offsetWidth;
    const maxY = window.innerHeight - els.codePopupModal.offsetHeight;
    els.codePopupModal.style.left = Math.max(0, Math.min(maxX, e.clientX - codePopupDrag.startX)) + "px";
    els.codePopupModal.style.top = Math.max(0, Math.min(maxY, e.clientY - codePopupDrag.startY)) + "px";
  }
});

document.addEventListener("mouseup", () => {
  if (vizDrag.active) {
    vizDrag.active = false;
    els.vizModalHead.style.cursor = "";
  }
  if (codePopupDrag.active) {
    codePopupDrag.active = false;
    els.codePopupHeader.style.cursor = "";
  }
});

// Draggable Try It popup — drag by the header (skip button clicks)
els.codePopupHeader.addEventListener("mousedown", (e) => {
  if (e.button !== 0 || e.target.closest("button")) return;
  e.preventDefault();
  const rect = els.codePopupModal.getBoundingClientRect();
  els.codePopupModal.style.transform = "none";
  els.codePopupModal.style.top = rect.top + "px";
  els.codePopupModal.style.left = rect.left + "px";
  codePopupDrag.active = true;
  codePopupDrag.startX = e.clientX - rect.left;
  codePopupDrag.startY = e.clientY - rect.top;
  els.codePopupHeader.style.cursor = "grabbing";
});

// "Try it" delegation — opens popup in place, no page scroll
// Also handles lesson tip card dismiss
els.lessonSections.addEventListener("click", (e) => {
  if (e.target.closest(".lesson-tip-dismiss")) {
    document.getElementById("lessonTipCard")?.remove();
    localStorage.setItem("pySkillLabTipDismissed", "1");
    return;
  }
  const btn = e.target.closest(".lesson-try-btn");
  if (!btn) return;
  openCodePopup(btn.dataset.code);
});

// Try-it modal controls
if (els.codePopupClose) els.codePopupClose.addEventListener("click", closeCodePopup);
if (els.codePopupMaxBtn) els.codePopupMaxBtn.addEventListener("click", toggleCodePopupMax);
if (els.codePopup) els.codePopup.addEventListener("click", (e) => { if (e.target === els.codePopup) closeCodePopup(); });
els.codePopupRunBtn.addEventListener("click", runCodePopup);
els.codePopupVizBtn.addEventListener("click", () => openVisualizer(els.codePopupEditor.value, els.codePopupVizBtn));
els.codePopupAiBtn.addEventListener("click", () => askInlinePopup(
  "Review this code. Explain what it does and whether there are any mistakes. If there are errors, explain exactly how to fix them."
));
els.codePopupClearBtn.addEventListener("click", () => {
  els.codePopupEditor.value = "";
  els.codePopupOutput.textContent = "Ready.";
  els.codePopupEditor.focus();
});
els.codePopupEditor.addEventListener("keydown", (e) => {
  if (e.key === "Tab") {
    e.preventDefault();
    const s = els.codePopupEditor.selectionStart;
    const en = els.codePopupEditor.selectionEnd;
    els.codePopupEditor.value = `${els.codePopupEditor.value.slice(0, s)}    ${els.codePopupEditor.value.slice(en)}`;
    els.codePopupEditor.selectionStart = els.codePopupEditor.selectionEnd = s + 4;
  }
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    e.preventDefault();
    runCodePopup();
  }
});

// ---------------------------------------------------------------------------
// Mobile topic list toggle
// ---------------------------------------------------------------------------

const _topicsToggle = document.getElementById("topicsToggle");
const _topicList = document.getElementById("topicList");

function _collapseTopicList() {
  if (!_topicsToggle) return;
  _topicList.classList.add("topics-collapsed");
  _topicsToggle.setAttribute("aria-expanded", "false");
  _topicsToggle.textContent = "Topics ▸";
}

function _expandTopicList() {
  if (!_topicsToggle) return;
  _topicList.classList.remove("topics-collapsed");
  _topicsToggle.setAttribute("aria-expanded", "true");
  _topicsToggle.textContent = "Topics ▾";
}

if (_topicsToggle) {
  _topicsToggle.addEventListener("click", () => {
    if (_topicList.classList.contains("topics-collapsed")) {
      _expandTopicList();
    } else {
      _collapseTopicList();
    }
  });
}

// Collapse topic list when viewport shrinks to mobile width mid-session
window.addEventListener("resize", () => {
  if (!_topicsToggle) return;
  if (window.innerWidth <= 1020 && !_topicList.classList.contains("topics-collapsed")) {
    _collapseTopicList();
  }
});

// ---------------------------------------------------------------------------
// AI settings popup
// ---------------------------------------------------------------------------

const _aiSettingsBtn = document.querySelector("#aiSettingsBtn");
const _aiSettingsPanel = document.querySelector("#aiSettingsPanel");

function _reclampPanel() {
  if (_aiSettingsPanel.hidden) return;
  const top = parseFloat(_aiSettingsPanel.style.top) || 0;
  const panelH = _aiSettingsPanel.offsetHeight;
  const clamped = Math.max(8, Math.min(top, window.innerHeight - panelH - 8));
  if (clamped !== top) _aiSettingsPanel.style.top = `${clamped}px`;
}

function _updateSettingsBtnLabel() {
  if (!_aiSettingsBtn) return;
  const provider = els.provider.value || "Ollama";
  const model = els.model.value || "";
  const label = model ? `⚙ ${provider} · ${model.length > 16 ? model.slice(0, 16) + "…" : model}` : `⚙ ${provider}`;
  _aiSettingsBtn.textContent = label;
}

_aiSettingsBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  if (!_aiSettingsPanel.hidden) {
    _aiSettingsPanel.hidden = true;
    return;
  }
  const rect = _aiSettingsBtn.getBoundingClientRect();
  const sidebarEl = document.querySelector(".sidebar");
  // Measure from the sidebar's own edge, not the trigger button's — the button
  // doesn't span the sidebar's full width, so using its rect let the panel land
  // inside the sidebar at wide viewports.
  const sidebarRight = sidebarEl ? sidebarEl.getBoundingClientRect().right : rect.right;
  const panelW = 280;
  const spaceRight = window.innerWidth - sidebarRight - 16;
  _aiSettingsPanel.style.width = `${panelW}px`;
  if (spaceRight >= panelW) {
    // Enough room to the right of the sidebar — open there so it doesn't cover the topic list
    _aiSettingsPanel.style.bottom = "auto";
    _aiSettingsPanel.style.left = `${sidebarRight + 8}px`;
    _aiSettingsPanel.style.top = `${rect.top}px`;
    _aiSettingsPanel.hidden = false;
    // Clamp after render so Save & Apply is never pushed below the viewport
    const panelH = _aiSettingsPanel.offsetHeight;
    _aiSettingsPanel.style.top = `${Math.max(8, Math.min(rect.top, window.innerHeight - panelH - 8))}px`;
  } else {
    // Narrow window fallback — position above or below button, clamped to viewport
    _aiSettingsPanel.style.top = "0";
    _aiSettingsPanel.style.bottom = "auto";
    _aiSettingsPanel.style.width = `${Math.min(panelW, window.innerWidth - 16)}px`;
    _aiSettingsPanel.hidden = false;
    const panelH2 = _aiSettingsPanel.offsetHeight;
    const panelW2 = _aiSettingsPanel.offsetWidth;
    const topPos = rect.top - 8 >= panelH2
      ? rect.top - panelH2 - 8
      : Math.min(rect.bottom + 8, window.innerHeight - panelH2 - 8);
    _aiSettingsPanel.style.top = `${Math.max(8, topPos)}px`;
    _aiSettingsPanel.style.left = `${Math.max(8, Math.min(rect.left, window.innerWidth - panelW2 - 8))}px`;
  }
});

async function testAiProviderConnection() {
  const testBtn = document.querySelector("#aiSettingsTestBtn");
  const local = isLocalAiProvider();
  const originalText = local ? "Test selected model" : "Verify provider";
  if (!els.model.value.trim()) {
    setAiSettingsStatus(
      "warn",
      "Choose a model first",
      local ? "Click Show local models, then choose one from the Model dropdown." : "Type the model name you want this provider to use."
    );
    return;
  }

  testBtn.textContent = local ? "Testing model..." : "Verifying...";
  testBtn.disabled = true;
  setAiSettingsStatus(
    "",
    local ? "Testing selected model..." : "Verifying provider...",
    local
      ? "Sending a short prompt to the selected local model. First local replies can take longer while the model loads."
      : "Sending a tiny health-check prompt to the selected model. This should finish quickly."
  );
  try {
    const apiKey = els.apiKey.value.trim();
    const saveResult = await saveAiSettingsToServer({
      includeKey: !!apiKey && !local,
      timeoutMs: 5000,
    });
    if (!saveResult.ok) {
      setAiSettingsStatus(
        "error",
        "Could not save AI settings",
        saveResult.error || "The provider check was not run because settings could not be written to .env."
      );
      return;
    }

    const result = await postJsonWithTimeout("/api/ai-coach", {
      provider: els.provider.value,
      model: els.model.value,
      endpoint: els.endpoint.value,
      api_key: els.apiKey.value,
      topic_id: "",
      exercise_id: "",
      code: "",
      run_result: {},
      question: "Reply exactly: Ready.",
      mode: "chat",
      purpose: "provider_test",
      max_tokens: 64,
      chat_history: [],
    }, local ? AI_REQUEST_TIMEOUT_MS : AI_PROVIDER_TEST_TIMEOUT_MS);
    if (!result.ok) {
      setAiSettingsStatus(
        "error",
        local ? "Model did not reply" : "Provider not verified",
        `${result.error || "Could not complete a test reply."}${local ? _localProviderWarmupHint() : ""}`
      );
    } else {
      setAiSettingsStatus(
        "ok",
        local ? "Selected model replied" : "Provider verified",
        local ? "This local model is ready for AI Coach and Ask AI." : "This provider is ready for AI Coach and Ask AI."
      );
      saveAiSettings();
    }
  } catch (err) {
    const message = String(err).includes("timed out")
      ? (
          local
            ? `Request timed out.${_localProviderWarmupHint()}`
            : "Provider check timed out. Verify uses a tiny prompt; check the API key, model name, endpoint, network/provider status, or try a stable fast model your account can access."
        )
      : (err.message || "Connection failed");
    setAiSettingsStatus("error", local ? "Model test failed" : "Provider check failed", message);
  }
  testBtn.textContent = originalText;
  testBtn.disabled = false;
  requestAnimationFrame(_reclampPanel);
}

document.querySelector("#aiSettingsTestBtn").addEventListener("click", testAiProviderConnection);

document.querySelector("#aiSettingsSaveBtn").addEventListener("click", async () => {
  const saveBtn = document.querySelector("#aiSettingsSaveBtn");
  saveBtn.textContent = "Checking…";
  saveBtn.disabled = true;

  if (isLocalAiProvider()) {
    // Local providers: must discover installed models before saving.
    const refresh = await loadModels({ persistOnSuccess: false });
    if (!refresh.ok) {
      saveBtn.textContent = "Save failed";
      saveBtn.disabled = false;
      setCoachStatus(`Settings not saved — ${refresh.error || "model refresh failed"}`);
      setAskAiStatus(`Settings not saved — ${refresh.error || "model refresh failed"}`);
      return;
    }
  } else {
    // API providers: the user types the model name — never call loadModels here.
    // loadModels does an async fetch that can overwrite the field before saveAiSettings runs.
    // Verify provider is the right tool for validation; Save just persists the current values.
    const model = els.model.value.trim();
    if (!model) {
      setAiSettingsStatus("warn", "Model required", "Type the model name your API account can use, then save.");
      saveBtn.textContent = "Save & Apply";
      saveBtn.disabled = false;
      return;
    }
    preferredModel = model;
  }

  saveAiSettings();
  const apiKey = els.apiKey.value.trim();
  const serverSave = await saveAiSettingsToServer({
    includeKey: !!apiKey && !isLocalAiProvider(),
    timeoutMs: 5000,
  });
  if (!serverSave.ok) {
    saveBtn.textContent = "Save failed";
    saveBtn.disabled = false;
    setAiSettingsStatus(
      "error",
      "Could not save AI settings",
      serverSave.error || "The provider settings could not be written to .env."
    );
    return;
  }
  const provider = els.provider.value;
  const model = els.model.value;
  setCoachStatus(`${provider} / ${model || "no model selected"}`);
  setAskAiStatus(`${provider} / ${model || "no model selected"}`);
  saveBtn.textContent = "✓ Saved";
  setTimeout(() => {
    _aiSettingsPanel.hidden = true;
    saveBtn.textContent = "Save & Apply";
    saveBtn.disabled = false;
    _updateSettingsBtnLabel();
    const s = document.querySelector("#aiSettingsTestStatus");
    if (s) { s.hidden = true; s.textContent = ""; }
  }, 900);
});

document.addEventListener("click", (e) => {
  if (!_aiSettingsPanel.hidden && !_aiSettingsPanel.contains(e.target) && e.target !== _aiSettingsBtn) {
    _aiSettingsPanel.hidden = true;
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  if (!els.vizOverlay.hidden) return; // viz overlay handles its own Escape
  if (els.askAiPanel && !els.askAiPanel.hidden) { closeAskAiPanel(); return; }
  if (!els.codePopup.hidden) { closeCodePopup(); return; }
  if (!_aiSettingsPanel.hidden) { _aiSettingsPanel.hidden = true; _aiSettingsBtn.focus(); }
});

// ---------------------------------------------------------------------------
// Inline AI — Try It popup and Visualizer
// ---------------------------------------------------------------------------

async function askInlinePopup(question) {
  const code = els.codePopupEditor.value.trim();
  const output = els.codePopupOutput.textContent;
  const hasOutput = output && output !== "Ready.";
  let full = question;
  if (code) full += `\n\nCode:\n\`\`\`python\n${code}\n\`\`\``;
  if (hasOutput) full += `\n\nOutput:\n${output.slice(0, 800)}`;
  await askFloatingAi(full, { includeTopicContext: true });
}

async function askInlineViz(question) {
  const code = vizState.lines.join("\n");
  const step = vizState.index >= 0 ? vizState.steps[vizState.index] : null;
  const builtInNote = visualizerBuiltInErrorNote(vizState.error);
  if (builtInNote && !step) {
    els.vizNote.innerHTML = `<span class="viz-ai-badge">Runner</span> ${escapeHtml(builtInNote)}`;
    return;
  }
  let ctx = `\n\nCode:\n\`\`\`python\n${code}\n\`\`\``;
  if (vizState.error) ctx += `\n\nError: ${vizState.error}`;
  if (step) {
    const lineCode = (vizState.lines[step.line - 1] || "").trim();
    const varsStr = Object.entries(step.vars || {}).map(([k, v]) => `${k} = ${pyStringify(v)}`).join(", ") || "none";
    ctx += `\n\nCurrently on line ${step.line}: \`${lineCode}\`\nVariables: ${varsStr}`;
  }
  els.vizNote.innerHTML = `<span class="viz-ai-badge">AI</span> I sent this step's context to Ask AI.`;
  await askFloatingAi(question + ctx, { includeTopicContext: true });
}

// ---------------------------------------------------------------------------
// Selection → Ask AI popover
// ---------------------------------------------------------------------------

let _selectionPopover = null;
let _quotedText = "";

function _ensurePopover() {
  if (_selectionPopover) return _selectionPopover;
  _selectionPopover = document.createElement("button");
  _selectionPopover.className = "selection-popover";
  _selectionPopover.type = "button";
  _selectionPopover.textContent = "Ask AI";
  _selectionPopover.setAttribute("aria-label", "Ask AI about the selected text");
  document.body.appendChild(_selectionPopover);

  _selectionPopover.addEventListener("mousedown", (e) => e.preventDefault());

  _selectionPopover.addEventListener("click", () => {
    const text = _quotedText;
    if (!text) return;
    _quotedText = "";
    _hideSelectionPopover();
    window.getSelection()?.removeAllRanges();

    const displayText = text.length > 300 ? text.slice(0, 300) + "…" : text;
    const question = `Explain this: "${displayText}"`;

    // Send selected text to the floating Ask AI messenger without moving the learner.
    if (!els.vizOverlay.hidden) {
      askInlineViz(question);
      return;
    }
    if (!els.codePopup.hidden) {
      askInlinePopup(question);
      return;
    }
    askFloatingAi(question, { includeTopicContext: true });
  });

  return _selectionPopover;
}

function _showSelectionPopover(rect) {
  const popover = _ensurePopover();
  const POPOVER_HEIGHT = 36;
  const GAP = 10;
  popover.style.top = `${Math.max(8, rect.top - POPOVER_HEIGHT - GAP)}px`;
  popover.style.left = `${rect.left + rect.width / 2}px`;
  popover.classList.add("visible");
}

function _hideSelectionPopover() {
  _selectionPopover?.classList.remove("visible");
}

document.addEventListener("mouseup", (e) => {
  if (e.target.closest(".selection-popover")) return;
  if (e.target.closest("textarea, input, select, .cm-editor")) return;

  requestAnimationFrame(() => {
    const selection = window.getSelection();
    const text = selection?.toString().trim() ?? "";
    if (text.length >= 5 && selection.rangeCount > 0) {
      const rect = selection.getRangeAt(0).getBoundingClientRect();
      if (rect.width > 0 || rect.height > 0) {
        _quotedText = text;
        _showSelectionPopover(rect);
        return;
      }
    }
    _quotedText = "";
    _hideSelectionPopover();
  });
});

document.addEventListener("mousedown", (e) => {
  if (e.target.closest(".selection-popover")) return;
  _hideSelectionPopover();
});

document.addEventListener("selectionchange", () => {
  if (!window.getSelection()?.toString().trim()) {
    _quotedText = "";
    _hideSelectionPopover();
  }
});

document.addEventListener("scroll", _hideSelectionPopover, { passive: true, capture: true });

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

async function initAiSettings() {
  loadAiSettings();
  updateAiSettingsMode();
  await loadModels({ notify: false });
  _updateSettingsBtnLabel();
  await loadServerAiSettings();
  _updateSettingsBtnLabel();
  maybeShowAiOnboarding();
}

document.documentElement.classList.remove("dark");
localStorage.setItem("pySkillLabTheme", "light");
initAiSettings();
renderAskAiMessages();
boot();
