---
name: write-course-pages
description: Write the course map and the mind map for one Study Notebook course, from its finished module pages and profile. Run after every module page of the course exists.
---

The repo root is two folders above this file. The course folder is `<data_root>/pages/<course>/`.

1. **Course map.**
   - Read `<repo root>/prompts/course-page.md`, plus the `## Course map` part of the course's profile (and `exam.md` when `flags.exam` is true).
   - Inputs: every `mNN.md` in the course folder, and `profile.json`.
   - Output: `course.md` in the course folder.
2. **Mind map.**
   - Read `<repo root>/prompts/mindmap.md`, plus the `## Mind map` part of the profile.
   - Same inputs.
   - Output: `mindmap.md` in the course folder.
3. Write only these two files. If you are a subagent and can start your own, the two pages may be written in parallel.
4. Reply in at most 2 lines: what each page holds.

Never name an output `summary.md` or `report.md`.
