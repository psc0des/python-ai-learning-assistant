"""Typed domain models for Python Skill Lab.

Uses dataclasses to keep the project dependency-free while providing
type safety, validation, and self-documenting structure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Content models
# ---------------------------------------------------------------------------

@dataclass
class DocLink:
    """An external documentation reference."""
    label: str
    url: str


@dataclass
class LessonSection:
    """One titled section inside a topic's lesson tab."""
    title: str
    body: str


@dataclass
class Topic:
    """A single learning topic (e.g. 'Python Basics', 'FastAPI')."""
    id: str
    track: str
    title: str
    level: str
    intro: str
    mental_model: str
    syntax: str
    example: str
    must_know: list[str] = field(default_factory=list)
    common_traps: list[str] = field(default_factory=list)
    interview: list[str] = field(default_factory=list)
    docs: list[dict[str, str]] = field(default_factory=list)
    real_world: list[str] = field(default_factory=list)
    outcome: str = ""
    lesson_sections: list[dict[str, str]] = field(default_factory=list)

    # Populated at load time from DIRECTIONAL_OVERVIEWS
    intro_overview: str = ""


@dataclass
class TestCase:
    """A single test case for an exercise."""
    label: str
    call: str
    expected: Any


@dataclass
class Exercise:
    """A coding lab exercise with starter code, tests, and hints."""
    id: str
    topic_id: str
    title: str
    difficulty: str
    prompt: str
    starter: str
    tests: list[dict[str, Any]] = field(default_factory=list)
    hint: str = ""
    solution: str = ""
    explanation: str = ""
    difficulty_order: int = 0


@dataclass
class PracticeQuestion:
    """A single multiple-choice practice question."""
    question: str
    options: list[str]
    answer: int
    explanation: str


@dataclass
class PracticeTest:
    """A set of practice questions for one topic."""
    topic_id: str
    questions: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Runtime models
# ---------------------------------------------------------------------------

@dataclass
class RunRequest:
    """A request to execute learner code."""
    code: str
    exercise_id: str

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> RunRequest:
        return cls(
            code=str(payload.get("code", "")),
            exercise_id=str(payload.get("exercise_id", "")),
        )


@dataclass
class TestResult:
    """Result of running one test case."""
    label: str
    call: str
    expected: Any
    actual: Any
    printed: str
    passed: bool


@dataclass
class RunResult:
    """Full result of running learner code."""
    ok: bool
    stdout: str
    stderr: str
    tests: list[dict[str, Any]] = field(default_factory=list)
    feedback: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "tests": self.tests,
            "feedback": self.feedback,
        }


@dataclass
class CoachRequest:
    """A request to the AI coach."""
    provider: str
    api_key: str
    model: str
    endpoint: str
    code: str
    topic_id: str
    exercise_id: str
    run_result: dict[str, Any]
    question: str
    chat_history: list[dict[str, Any]]

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> CoachRequest:
        return cls(
            provider=str(payload.get("provider", "ollama")).lower(),
            api_key=str(payload.get("api_key", "")),
            model=str(payload.get("model", "")).strip(),
            endpoint=str(payload.get("endpoint", "")).strip(),
            code=str(payload.get("code", "")),
            topic_id=str(payload.get("topic_id", "")),
            exercise_id=str(payload.get("exercise_id", "")),
            run_result=payload.get("run_result", {}),
            question=str(payload.get("question", "")).strip(),
            chat_history=payload.get("chat_history", []),
        )


@dataclass
class CoachResult:
    """Result from the AI coach."""
    ok: bool
    answer: str
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"ok": self.ok, "answer": self.answer}
        if self.error:
            result["error"] = self.error
        return result


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

REQUIRED_TOPIC_FIELDS = {"id", "track", "title", "level", "intro", "mental_model", "syntax", "example"}
REQUIRED_EXERCISE_FIELDS = {"id", "topic_id", "title", "difficulty", "prompt", "starter", "tests"}


def validate_topic(topic: dict[str, Any]) -> list[str]:
    """Return a list of missing required fields for a topic dict."""
    return [f for f in REQUIRED_TOPIC_FIELDS if f not in topic or not topic[f]]


def validate_exercise(exercise: dict[str, Any]) -> list[str]:
    """Return a list of missing required fields for an exercise dict."""
    return [f for f in REQUIRED_EXERCISE_FIELDS if f not in exercise]


# Phase-2 quality-gate baselines for reference topics.
REFERENCE_MIN_LABS = 5
REFERENCE_MIN_QUESTIONS = 8


def validate_content_at_startup(
    topics: list[dict[str, Any]],
    exercises: list[dict[str, Any]],
    practice_tests: list[dict[str, Any]],
) -> list[str]:
    """Validate all content and return a list of warnings.

    This version preserves legacy structural checks and adds stronger guidance
    for topics marked as `quality_status: reference`.
    """
    warnings: list[str] = []

    topic_ids = set()
    exercises_by_topic: dict[str, int] = {}
    questions_by_topic: dict[str, int] = {}

    for topic in topics:
        missing = validate_topic(topic)
        if missing:
            warnings.append(f"Topic '{topic.get('id', '?')}' missing fields: {missing}")
        topic_ids.add(topic.get("id"))

    exercise_topic_ids = set()
    for exercise in exercises:
        missing = validate_exercise(exercise)
        if missing:
            warnings.append(f"Exercise '{exercise.get('id', '?')}' missing fields: {missing}")
        tid = exercise.get("topic_id")
        if tid and tid not in topic_ids:
            warnings.append(f"Exercise '{exercise.get('id')}' references unknown topic '{tid}'")
        exercise_topic_ids.add(tid)
        if tid:
            exercises_by_topic[tid] = exercises_by_topic.get(tid, 0) + 1

    for topic_id in topic_ids:
        if topic_id not in exercise_topic_ids:
            warnings.append(f"Topic '{topic_id}' has no exercises")

    test_topic_ids = {t.get("topic_id") for t in practice_tests}
    for topic_id in topic_ids:
        if topic_id not in test_topic_ids:
            warnings.append(f"Topic '{topic_id}' has no practice test")

    for test in practice_tests:
        questions = test.get("questions", [])
        tid = test.get("topic_id")
        if tid:
            questions_by_topic[tid] = len(questions)
        if len(questions) < 3:
            warnings.append(
                f"Practice test for '{test.get('topic_id')}' has only {len(questions)} question(s); recommend 5+"
            )

    for topic in topics:
        topic_id = topic.get("id")
        quality_status = topic.get("quality_status", "draft")
        labs_count = exercises_by_topic.get(topic_id, 0)
        question_count = questions_by_topic.get(topic_id, 0)

        if quality_status == "reference":
            if labs_count < REFERENCE_MIN_LABS:
                warnings.append(
                    f"Reference topic '{topic_id}' has {labs_count} lab(s); needs {REFERENCE_MIN_LABS}+"
                )
            if question_count < REFERENCE_MIN_QUESTIONS:
                warnings.append(
                    f"Reference topic '{topic_id}' has {question_count} question(s); needs {REFERENCE_MIN_QUESTIONS}+"
                )

            lesson_sections = topic.get("lesson_sections", [])
            sourced_sections = sum(1 for section in lesson_sections if section.get("source_url"))
            if lesson_sections and sourced_sections < len(lesson_sections):
                warnings.append(
                    f"Reference topic '{topic_id}' has missing source_url in lesson sections "
                    f"({sourced_sections}/{len(lesson_sections)} sourced)"
                )
        elif quality_status != "draft":
            warnings.append(
                f"Topic '{topic_id}' has unknown quality_status '{quality_status}'; "
                "expected 'reference' or 'draft'"
            )

    return warnings

