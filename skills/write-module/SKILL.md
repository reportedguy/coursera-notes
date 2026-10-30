---
name: write-module
description: Write one teach-first Study Notebook module page from that module's lesson packs, following the course's profile. Use one per module.
---

The repo root is two folders above this file.

1. Read `<repo root>/prompts/module-page.md`. Then read the course's profile file, `<repo root>/prompts/profiles/<type>.md`, where `<type>` comes from `profile.json`. Also read `<repo root>/prompts/profiles/exam.md` when `flags.exam` is true. The profile's `## Module page` part fills the `{{PROFILE}}` slot.
2. Inputs, from the plan:
   - every file in this module's `packs` list. Read each one in full, and open each contact sheet image a pack names.
   - the course's `profile.json`.
   - the course's `brief` file, for lesson weights (video minutes and quizzes per lesson).
3. Output: this module's `output` path (`<data_root>/pages/<course>/mNN.md`). Write only this file.
4. Before saving, run the prompt's self-check. Every number, count and named list must match the packs exactly. Invented counts are the most common error.
5. Reply in at most 3 lines: the path, the topics covered, and anything you left out and why.
