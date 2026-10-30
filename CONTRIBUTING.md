# Contributing to coursera-notes

Thanks for helping. This guide covers setup, the one hard rule, and the two most useful kinds of contribution: course-type profiles and agent install reports.

## The one hard rule
**Never commit course content.** No transcripts, readings, quiz text, captured pages, or notebooks built from a real course. That includes inside tests, issues and screenshots. Use invented text, like the samples in `examples/sample-courses/`. The pre-commit hook blocks the common cases, but it can't catch everything, so the rule is on you.

## Setup
```bash
uv sync --all-extras
```
```bash
uv run pre-commit install
```
```bash
uv run pytest
```
The tests are offline: no network and no Coursera.

## Where things live
- **`src/sv/`**: the `notebook` CLI. `coursera_adapter.py` is the only module that knows Coursera URLs, and `browser.py` holds pacing and the safety stops.
- **`skills/` and `agents/`**: what the AI agent follows.
- **`prompts/`**: the writing rules. `module-page.md`, `course-page.md` and `mindmap.md` are the base, and `profiles/<type>.md` adapt them to a kind of course.
- **`src/sv/template.html`**: the notebook app.

## Adding or improving a course-type profile
1. Copy the closest file in `prompts/profiles/` and keep its sections: `For:`, `Role:`, `## Important means`, `## Module page`, `## Example format`, `## Course map`, `## Mind map` and `## Questions`.
2. Add the new type to the decision list in `prompts/course-brief.md`.
3. Write a small sample course in `examples/sample-courses/<name>/` (original text) and run `uv run python tools/build_demo.py` to check how it renders.
4. In the PR, show one before/after module page from a course you're enrolled in. **Describe it, don't paste it**: say which sections appeared and what changed.

## Changing the safety layer
Changes to `browser.py` (pacing, stops) or to the read-only guard in `coursera_adapter.py` (`GRAPHQL_ALLOW`, the non-GET check) need a clear reason in the PR, and a reviewer will be strict. Changes that make the tool more conservative are always welcome.

## Demo images
After changing `template.html` or the samples, regenerate them:
```bash
uv run python tools/build_demo.py && uv run python tools/capture_demo.py
```

## Pull requests
- Keep each PR to one change, and make sure tests pass.
- Follow the surrounding style: short functions, comments only for the non-obvious "why".
- Fill in the PR template's checklist.
