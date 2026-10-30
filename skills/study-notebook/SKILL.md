---
name: study-notebook
description: Turn a Coursera course, specialization or professional certificate the user is enrolled in into one editable Study Notebook (teach-first module pages, course map, mind map, question practice), adapted to the course type. Use when the user gives a Coursera link or asks for notes, a study guide or a notebook from a Coursera course.
---

# Study Notebook

The repo root is two folders above this file. Run every command from it as `uv run --project "<repo root>" notebook …`, abbreviated below as `notebook`. If `uv` is missing, tell the user to install it from https://docs.astral.sh/uv/ and stop.

Work in this order. Do not explore files beyond what each step names: every path you need comes from `plan.json`.

## 1. Setup (once per computer)
- `notebook doctor`. If the browser row says MISS, ask the user to install Google Chrome or Microsoft Edge.
- If the login row says to run `notebook login`, run it and tell the user: "A browser window is opening. Sign in to Coursera there, then close the window." **Never ask for, type or store the user's password.** Signing in happens only in that window.

## 2. Fetch and prepare (no tokens)
- Ask for the course link if the user hasn't given one. A course link (`/learn/...`), a specialization or a professional certificate link all work.
- Run `notebook add "<link>"` in the background. Add `--slides` only if the user asks for slide images and `doctor` found ffmpeg. Add `--modules 1-2` only if the user wants part of a course.
  - A long course takes 10–40 minutes. Fetching is paced on purpose, to stay gentle on Coursera.
- It prints a JSON plan, also saved at `<data_root>/work/plan.json`. Read it from there.
- **If the output contains `STOPPED`, stop.** Tell the user exactly what it said, such as a login expiry, captcha, HTTP 429 or 403. Never retry on your own. Progress is saved, so re-running the same command later continues where it left off.
- A course with an `error` (usually "not enrolled") is skipped. Tell the user to enroll on Coursera themselves, then re-run. Never enroll, submit or complete anything on the user's behalf.

## 3. Course brief (one call per course)
For each course in the plan, follow `skills/course-brief/SKILL.md`, with input `brief` and output `profile`. Skip a course whose `profile.json` already exists, unless the user asked for a different type.
- If the user named a type, such as "this is a programming course", pass it in as the decision.

## 4. Pages
For each course, write the following. Skip any output file that already exists unless the user asked to rewrite it, because the user may have edited it.
1. **Module pages:** one per module in `modules`, following `skills/write-module/SKILL.md`, with that module's `packs`, the course `profile` and `output`.
2. **Course pages:** after all of the course's modules exist, follow `skills/write-course-pages/SKILL.md` for the course map and the mind map.
3. **Questions:** if the course's `qa_candidates` file is not `[]`, follow `skills/curate-questions/SKILL.md`, then run `notebook qa <course> --apply`.

How to run them:
- **If you can start subagents** (Claude Code: the `page-writer` agent), run the module pages in parallel in the background, one agent per module. Give each agent the skill path and its inputs. When they finish, check each output file exists on disk, because an agent may report a write that didn't happen.
- **Otherwise**, write them one after another yourself, following the same skill files.

## 5. Build and deliver
- `notebook build`. If this notebook is already published as an artifact, first save the live artifact's HTML and run `notebook build --live "<that file>"`, so the user's edits are kept.
- The result is `notebook` in the plan, a single self-contained HTML file. Tell the user its full path. It opens in any browser, offline, any time. Edits save in that browser, and **Save copy** downloads the notebook with the edits included.
- **If you have a tool that publishes HTML as an artifact** (the Claude app), also publish that file and give the user the link.

## 6. Report (short)
- Pages written per course, and the type each course was classified as.
- The question count per course. Where it is 0, say that question practice comes from the user's own quiz attempts: do the quizzes on Coursera, then ask for an update.
- Locked items from the plan's `locked` list. These are usually exemplars that unlock after the user submits the activity. An update picks them up later.

## Updating later
Re-run `notebook add "<same link>"`. Items already fetched are not fetched again, and locked items and new quiz attempts are picked up. Then redo step 3 only for new courses, and in step 4 write only missing pages, plus the module pages whose packs gained new items. Re-run step 4.3 when `qa_candidates` grew. Finish with step 5 (with `--live` if published).
