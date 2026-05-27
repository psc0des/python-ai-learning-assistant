"""Baseline quality-gate tests for curriculum maturity."""

from collections import Counter

from content_loader import load_content


def test_reference_topics_meet_baseline():
    loaded = load_content()
    labs_per_topic = Counter(ex["topic_id"] for ex in loaded.exercises)
    questions_per_topic = {
        test["topic_id"]: len(test.get("questions", []))
        for test in loaded.practice_tests
    }

    reference_topics = [topic for topic in loaded.topics if topic.get("quality_status") == "reference"]
    assert reference_topics, "At least one topic should be marked as reference quality."

    for topic in reference_topics:
        tid = topic["id"]
        assert labs_per_topic.get(tid, 0) >= 5, f"Reference topic '{tid}' should have at least 5 labs."
        assert questions_per_topic.get(tid, 0) >= 8, (
            f"Reference topic '{tid}' should have at least 8 practice questions."
        )
        lesson_sections = topic.get("lesson_sections", [])
        sourced_sections = [section for section in lesson_sections if section.get("source_url")]
        assert len(sourced_sections) == len(lesson_sections), (
            f"Reference topic '{tid}' should have source_url for all lesson sections."
        )


def test_non_reference_topics_are_explicitly_draft():
    loaded = load_content()
    for topic in loaded.topics:
        if topic.get("quality_status") != "reference":
            assert topic.get("quality_status") == "draft", (
                f"Topic '{topic['id']}' should be marked as draft until fully upgraded."
            )

