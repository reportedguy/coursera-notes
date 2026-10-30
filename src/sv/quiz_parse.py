"""Turn QueryState + AssignmentFeedback responses into QuizQuestion records.

Correct answers come only from what your completed attempts reveal:
- checkbox: each option's `correctlyAnswered` says whether your handling of it was
  right, so correct options = (chosen and right) + (not chosen and wrong);
- single choice: if the question was marked CORRECT, your choice is the answer;
- otherwise the answer stays unknown and the question is left out of the quiz score.
"""

from __future__ import annotations

from selectolax.lexbor import LexborHTMLParser

from sv.models import QuizQuestion


def _text(content) -> str:
    if not content:
        return ""
    if isinstance(content, str):
        return content
    html = (content.get("htmlWithMetadata") or {}).get("html")
    if html:
        return LexborHTMLParser(html).text(separator=" ", strip=True)
    return LexborHTMLParser(content.get("cmlValue") or "").text(separator=" ", strip=True)


def _state(data: dict) -> dict:
    return (((data or {}).get("data") or {}).get("SubmissionState") or {}).get("queryState") or {}


def _response(part: dict):
    for key, val in part.items():
        if key.endswith("Response") and isinstance(val, dict):
            return key, val
    return None, {}


def parse(state: dict, feedback: dict | None = None) -> tuple[list[QuizQuestion], list[str]]:
    qs = _state(state)
    last = (qs.get("attempts") or {}).get("lastSubmission")
    if not last:
        return [], ["quiz_no_submission"]
    fb_parts = {p.get("partId"): p for p in ((_state(feedback).get("feedback") or {}).get("parts") or [])}
    sub_parts = (last.get("submission") or {}).get("parts") or []
    # Feedback parts carry the same questions with correctness; prefer them when present.
    parts = list(fb_parts.values()) or sub_parts

    out, flags = [], []
    for n, part in enumerate(parts, start=1):
        schema = part.get("questionSchema") or {}
        opts = schema.get("options") or []
        option_ids = [o.get("optionId") for o in opts]
        _, resp = _response(part)
        chosen = resp.get("chosen")
        answer_text = None
        if chosen is None:
            answer_text = _text(resp.get("answer") or resp.get("richText") or resp.get("plainText"))
        chosen_ids = chosen if isinstance(chosen, list) else ([chosen] if chosen else [])
        my = [option_ids.index(c) for c in chosen_ids if c in option_ids]

        pf = part.get("feedback") or {}
        correctness = pf.get("correctness")
        correct, source = None, "unknown"
        if opts and all("correctlyAnswered" in o for o in opts):
            correct = [i for i, o in enumerate(opts)
                       if (o["optionId"] in chosen_ids) == bool(o["correctlyAnswered"])]
            source = "shown"
        elif opts and correctness == "CORRECT":
            correct, source = my, "inferred-from-graded"

        notes = [_text(o.get("feedback")) for o in opts]
        feedback_text = " ".join(
            f"[{chr(65 + i)}] {t}" for i, t in enumerate(notes) if t
        ) or _text(pf.get("feedback")) or None
        typename = (part.get("__typename") or "").split("_")[-1]
        out.append(QuizQuestion(
            qid=f"q{n}",
            stem=_text(schema.get("prompt")),
            options=[_text(o.get("display")) for o in opts],
            my_answer=my if opts else answer_text,
            correct=correct,
            correct_source=source if opts else "unknown",
            feedback=(f"({typename}, {correctness}) " if correctness else f"({typename}) ") + (feedback_text or ""),
        ))
    if not fb_parts:
        flags.append("quiz_no_feedback")
    return out, flags
