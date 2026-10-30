from sv.normalize import parse_vtt, segment
from sv.paths import slugify, unique_names
from sv.quiz_parse import parse as parse_quiz

VTT = """WEBVTT

1
00:00:00.200 --> 00:00:03.840
Hello and welcome
to the first lesson.

2
00:00:03.840 --> 00:00:06.540
My name is Sam, and I
teach this course.

3
00:00:06.540 --> 00:00:30.000
This sentence runs long without a stop
"""


def test_parse_vtt_joins_lines():
    cues = parse_vtt(VTT)
    assert [c.text for c in cues][:2] == ["Hello and welcome to the first lesson.",
                                         "My name is Sam, and I teach this course."]
    assert cues[0].start == 0.2 and cues[1].end == 6.54


def test_segment_merges_until_sentence_end():
    segs = segment(parse_vtt(VTT))
    assert segs[0].text.endswith("teach this course.")
    assert segs[0].start == 0.2 and segs[0].end == 6.54
    assert len(segs) == 2


def test_slugify_windows_safe():
    assert slugify("A project manager’s role: CON?") == "a-project-managers-role-con"
    assert slugify("con") == "con-x"
    assert len(slugify("x" * 200)) == 50
    assert unique_names(["A", "a", "b"]) == ["A", "a-2", "b"]


def _state(parts):
    return {"data": {"SubmissionState": {"queryState": {"attempts": {"lastSubmission": {
        "submission": {"parts": parts}}}}}}}


def _fb(parts):
    return {"data": {"SubmissionState": {"queryState": {"feedback": {"parts": parts}}}}}


def test_quiz_checkbox_key_from_correctly_answered():
    part = {"partId": "p1", "__typename": "Submission_GradedCheckboxQuestion",
            "questionSchema": {"prompt": "Pick", "options": [
                {"optionId": "a", "display": "A", "correctlyAnswered": True},
                {"optionId": "b", "display": "B", "correctlyAnswered": True},
                {"optionId": "c", "display": "C", "correctlyAnswered": False}]},
            "checkboxResponse": {"chosen": ["a"]},
            "feedback": {"correctness": "PARTIALLY_CORRECT"}}
    qs, flags = parse_quiz(_state([part]), _fb([part]))
    # a chosen & right -> correct; b not chosen & right -> wrong option; c not chosen & wrong -> correct
    assert qs[0].correct == [0, 2] and qs[0].correct_source == "shown"
    assert qs[0].my_answer == [0] and flags == []


def test_quiz_single_choice_inferred_only_when_correct():
    def part(correctness):
        return {"partId": "p", "questionSchema": {"prompt": "Q", "options": [
                    {"optionId": "x", "display": "X"}, {"optionId": "y", "display": "Y"}]},
                "multipleChoiceResponse": {"chosen": "y"}, "feedback": {"correctness": correctness}}
    right, _ = parse_quiz(_state([part("CORRECT")]), _fb([part("CORRECT")]))
    wrong, _ = parse_quiz(_state([part("INCORRECT")]), _fb([part("INCORRECT")]))
    assert right[0].correct == [1] and right[0].correct_source == "inferred-from-graded"
    assert wrong[0].correct is None and wrong[0].correct_source == "unknown"
