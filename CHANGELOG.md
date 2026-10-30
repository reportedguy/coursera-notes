# Changelog

## [0.2.0] - 2026-10-31
First public release.

### Added
- `notebook add <link>` for a course, specialization or professional-certificate link: discover the courses, fetch read-only and paced, normalize, pack, extract questions, and write a syllabus brief plus `plan.json`.
- Course-type profiles (business, technical, quantitative, science, language, creative, humanities, career, plus an exam add-on), picked once per course by a short brief.
- Agent skills (`study-notebook`, `course-brief`, `write-module`, `write-course-pages`, `curate-questions`) and a `page-writer` subagent. Install as a Claude Code plugin, or use them from Codex and Gemini CLI.
- The notebook works offline as a single file: edits save in the browser, and **Save copy** downloads the notebook with them. It also works as a Claude artifact.
- Diagrams render in the browser, and code blocks are styled.
- Original sample courses, a live demo on GitHub Pages, and reproducible screenshot tooling.

### Changed
- The install is lighter: Quarto, Node and mermaid-cli are no longer needed, and slide frames (ffmpeg) are opt-in with `--slides`.
- The data folder defaults to `~/StudyNotebook`, and works on Windows, macOS and Linux.
