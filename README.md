# Study Notebook

Paste a Coursera link into your AI agent. You get back one editable notebook that teaches the course: someone who hasn't watched a single video can learn from it directly.

For every course it writes:
- **a page per module**: concepts explained from zero, frameworks, worked examples, checklists, a recap and a glossary
- **a course map**: how the whole course fits together, plus the takeaways worth keeping
- **a mind map**: the whole course at a glance, with each branch expandable
- **question practice**: the real quiz questions you've answered, with basic ones dropped. Click an option to check it.

There's no filler: every line has to teach something. Page structure follows the **course type**: a Python course gets runnable code and gotchas, a statistics course gets formulas and worked examples, a language course gets vocabulary and grammar tables, a business course gets frameworks and checklists.

The notebook is a single HTML file on your computer. Open it in any browser, offline, any time, and click anywhere to edit it, as in Notion. In the Claude app it can also be published as a private artifact.

## How it works

```
course link → notebook add  ─(your browser session, read-only, paced)→  transcripts, readings, PDFs, your quiz attempts
            → lesson packs  ─(your AI agent writes, guided by the course-type profile)→  pages
            → notebook build →  notebook.html
```

- **Code does all the mechanical work, at zero tokens:** fetching, cleaning transcripts, packing each lesson, slide frames, Q&A extraction and HTML assembly.
- **Your agent only writes the pages.** That's roughly 40–80k tokens per module, run in parallel where the agent supports it.

## Requirements
- [uv](https://docs.astral.sh/uv/getting-started/installation/), which also installs Python for you
- Google Chrome or Microsoft Edge
- An AI coding agent that can run commands: Claude Code, OpenAI Codex CLI or Gemini CLI. Web chat apps can't run it, because they can't open a browser on your computer.
- A Coursera account **enrolled** in the course
- Optional: [ffmpeg](https://ffmpeg.org/download.html), for slide images (`--slides`)

## Install

**Claude Code** (desktop app or CLI):
```
/plugin marketplace add reportedguy/study-notebook
/plugin install study-notebook@study-notebook
```
Then just ask: *"Make a study notebook from https://www.coursera.org/learn/…"*

**Codex CLI or Gemini CLI.** Clone the repo and start the agent inside it:
```bash
git clone https://github.com/reportedguy/study-notebook
```
```bash
cd study-notebook && codex
```
The agent reads `AGENTS.md` (Codex) or `GEMINI.md` (Gemini), which point it to the skills. Then ask the same question. These two agents are supported by design but not yet tested, so reports are welcome.

## First run
1. The agent runs `notebook login`. A browser window opens. **You** sign in to Coursera there, then close it. The tool never sees or stores your password; the session stays in a local browser profile.
2. It runs `notebook add "<link>"`.
   - Course, specialization and professional certificate links all work. A certificate is split into its courses.
   - Fetching is paced on purpose and takes about 10–40 minutes per course.
3. It classifies each course's type, writes the pages and builds `~/StudyNotebook/notebook/notebook.html`.

To update later, after more quizzes or newly unlocked items, ask the agent to update the notebook. Nothing is fetched twice, and your edits are kept.

## Course types

| Type | Pages centre on |
|---|---|
| business | Frameworks, blueprints and checklists, worked examples, mistakes |
| technical | Runnable code and commands, procedures, errors and gotchas, a cheat sheet |
| quantitative | Formulas with every symbol explained, worked examples step by step |
| science | Mechanisms as diagrams, cause and effect, compare/contrast tables |
| language | Vocabulary tables, grammar patterns, phrases by situation |
| creative | Principles, techniques, critique criteria, exercises |
| humanities | Arguments and positions, timelines, evidence |
| career | Playbooks, templates and scripts, do/don't pairs |
| + exam flag | Exam-objective mapping, trap callouts, harder practice |

The type is picked automatically. Override it by telling the agent, such as *"treat it as technical"*, or by editing `~/StudyNotebook/pages/<course>/profile.json`.

## Good to know
- **Question practice comes from your own attempts.** Do the quizzes on Coursera first. Unattempted quizzes have no answers to show.
- **Locked items are skipped** and picked up on the next update. These are usually activity exemplars, which unlock after you submit the activity.
- **Slide images** are opt-in (`--slides`, needs ffmpeg). Without them, pages still include the course's diagrams and reading images, plus diagrams the writer draws.
- **Data folder:** `~/StudyNotebook`. Change it with the `SV_DATA_ROOT` environment variable.

## Terms of use and safety: read this
Coursera's Terms of Use restrict automated access to the site. This tool is built to stay as gentle and as personal as possible, but **using it may still breach those terms, and your account is your responsibility.**
- **Personal study only.** It reads courses *you* are enrolled in, through *your* signed-in session.
- **Read-only.** It never submits, enrolls or changes anything. Only two read-only quiz queries are allowed; anything else is refused in code.
- **Paced like a person:** a few seconds between requests, periodic pauses and an hourly cap.
- **Stops instead of pushing:** on a login expiry, captcha, HTTP 429 or 403 it stops and tells you, and never retries on its own.
- **Your data stays local.** Nothing is uploaded anywhere except to your own AI agent while it writes. Don't share or publish notebooks made from paid course content.

This project isn't affiliated with or endorsed by Coursera.

## Commands
`notebook doctor` · `notebook login` · `notebook add <link> [--modules 1-3] [--slides]` · `notebook build [--live <saved artifact html>]`.
Advanced, for one course key: `ingest`, `normalize`, `media`, `pack`, `qa`.

Run without installing:
```bash
uvx --from git+https://github.com/reportedguy/study-notebook notebook doctor
```

## Develop
```bash
uv sync --all-extras
```
```bash
uv run pytest
```
```bash
uv run pre-commit install
```

## License
MIT
