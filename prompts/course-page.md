---
id: course-page@v3
---
# Course map

Input: the course's module pages (written with prompts/module-page.md) and the course's `profile.json` (path in your task; `<data_root>/pages/<course>/profile.json` if none is named). Output: ONE page that lets someone who hasn't taken the course see the whole course at once: what it teaches, how the parts connect, and what to use at work. It must also work as the refresher a reader comes back to.

Profile: the `## Course map` part of `prompts/profiles/<type>.md` fills the slot under Structure, followed by the `## Course map` part of `prompts/profiles/exam.md` when `flags.exam` is true. If the slot still reads `{{PROFILE}}` literally, read those files yourself. If base and profile conflict, the base wins.

Voice: as in module-page.md. Precise, plain sentences that each carry a fact. No warm-up, no filler.

Structure, in this order:

{{PROFILE}}

Rules: no word limit, but nothing that isn't in the module pages, no images, and no links. Give the most room to the profile's `emphasis` topics. Before saving, check every number, list count and named item against the module pages, as in module-page.md's self-check. Write to the output path in your task. Reply with one line: the section count.
