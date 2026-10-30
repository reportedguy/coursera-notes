# Agent instructions

This repo is **coursera-notes**, the Study Notebook tool. When the user gives a Coursera link or asks for notes from a Coursera course, read `skills/study-notebook/SKILL.md` and follow it exactly. The other skills in `skills/` are its steps.

If you cannot start subagents, do the per-module steps one after another yourself.

Rules that always hold:
- Never ask for, type or store the user's Coursera password. Sign-in happens only in the browser window that `notebook login` opens.
- Coursera access is read-only. Never enroll, submit, or complete anything on the user's behalf.
- When a command prints `STOPPED`, stop and tell the user what it said. Never retry automatically.
- Course content stays in the user's data folder (`~/StudyNotebook`). Never copy it into this repo.
