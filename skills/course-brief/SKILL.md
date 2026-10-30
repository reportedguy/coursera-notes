---
name: course-brief
description: Classify one Coursera course (business, technical, quantitative, science, language, creative, humanities or career, plus exam/code/formula flags) so every Study Notebook page follows the right structure. Input is the course's brief file; output is profile.json.
---

The repo root is two folders above this file.

1. Read `<repo root>/prompts/course-brief.md` and follow it exactly.
2. Input: the `brief` path from the plan (`<data_root>/work/brief/<course>.md`). It is your only source.
3. Output: the `profile` path from the plan (`<data_root>/pages/<course>/profile.json`). Write only this file.
4. If the user or the task already named the type, use it, and fill in the other fields from the brief.
5. Reply in one line: the type, the level, the flags set, and the reason.
