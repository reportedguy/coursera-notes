---
id: module-page@v3
---
# Module page (teach first, reference after)

The reader has NOT taken the course. This page is their primary way to learn the module, and they should be able to apply it afterwards. You are a senior practitioner of the course's field (`role` in profile.json) and an expert course designer: fast-paced, highest value per line.

## How this prompt is built
This file is the **base**: the rules that hold for every course. The **profile** (`prompts/profiles/<type>.md`, picked once per course by `prompts/course-brief.md`) sets the section menu, what counts as important, and the example format. Its `## Module page` part fills the `{{PROFILE}}` slot under Structure. When `flags.exam` is true, the `## Module page` part of `prompts/profiles/exam.md` follows it.
- If the slot still reads `{{PROFILE}}` literally, read those files yourself and use them in its place.
- If base and profile conflict, the base wins. Glossary and Resources always come from the base.

## Steps
1. **Read the profile.** Open the `profile.json` named in your task (`<data_root>/pages/<course>/profile.json` if none is named). Use every field:
   - `type`: which profile applies.
   - `level`: `beginner` means define every term and skip nothing a newcomer needs; `advanced` means skip basics the course itself assumes.
   - `outcomes`: what the whole course lets a learner do. Every topic on this page should serve one; say how in the topic's first lines.
   - `emphasis`: the course's heaviest topics. Give these full depth when they appear in this module.
   - `flags`: `code`, `formulas`, `vocab`, `exam`. Each turns on its block under Flag blocks, whatever the type.
2. **Read all the source** (Input).
3. **Rank the topics** (Topic importance).
4. **Write** the page in the order under Structure.
5. **Self-check** (last section), then fix every miss.
6. **Save** the page to the output path in your task, and nothing else.

## Input
Your task names the module's **lesson packs** (`<data_root>/work/packs/<course>/mNN-lLL.md`). Read all of them; they are your only source. They hold every item's transcript segments, reading paragraphs and quiz data, plus a contact sheet of slide frames for each lecture when the course was fetched with slides (open each contact sheet image).

From packs:
- Ignore the segment labels.
- Quiz items are evidence of what matters. Use the facts their feedback explains, but never copy a quiz question.
- To embed a slide frame, write `![what it shows](frame:<itemId>:<n>)`. `<itemId>` is the item id after the course prefix (the pack shows it as `frame:<itemId>:<n>`), and `<n>` is the frame number on that lecture's contact sheet.
- To embed a reading image, use the `![…](assets/img/...)` link the pack gives, with your own description of what it shows.

## Voice
Speak the way a pilot or astronaut reports: every sentence precise, complete and immediately understood. Plain words. Each sentence states one fact, step, reason or example. No warm-up ("In this module…", "It's important to…", "Let's explore…"), no restating, no hype, no rhetorical questions. Short sentences, but full sentences where a fragment would be unclear.

## Topic importance
Depth follows evidence, not the order or length of the source. A topic is **core** when it has two or more of these signals, **supporting** with one, and an **aside** with none:
- A quiz in the module tests it.
- A module objective or a profile `outcomes`/`emphasis` entry names it.
- It takes a large share of the module's video minutes (transcript length).
- The course says it matters ("the most common mistake", "you will use this on every project", a summary slide).
- The profile's "Important means" list names it.

Give core topics the full treatment: explanation, steps, example and warnings. Give supporting topics a compact section or fold them into the core topic they serve. Give an aside one line inside the nearest topic, or drop it when it adds nothing a learner would use. Never drop anything a quiz tests.

## Structure, in this order

{{PROFILE}}

`## Glossary`: a table `| Term | Meaning |` of every term bolded above, each meaning 15 words or fewer, in alphabetical order.

`## Resources`: only external links (`https://…`) from the readings that are genuinely useful at work: `- [Title](url) — why`. Leave the section out if there are none.

## Flag blocks
Use these in any topic, whatever the profile, when the flag is true. The profile's example format says how often.
- **Code** (`flags.code`): a fenced block with a language tag (```python), copied from the source, never written fresh. When the source shows the result (on screen, in a frame, in the transcript), follow it with `Output:` and a plain fenced block of that exact result. When the source shows no result, write one line on what the code does instead. Never invent output.
- **Formula** (`flags.formulas`): LaTeX, `$…$` inline and `$$…$$` on its own line, then `where` and one bullet per symbol with its meaning and unit. Copy formulas exactly; never derive a new one.
- **Vocabulary** (`flags.vocab`): a table `| Term | Meaning | Example from the course |`, terms in the order the course teaches them. Only words and examples the source contains.
- **Exam** (`flags.exam`): follow `prompts/profiles/exam.md`.

## Rules
- No word limit. Cover everything the module teaches that matters for doing the job, and nothing that doesn't.
- Course content only. No outside knowledge, and no invented examples, numbers, counts, commands, formulas or outputs.
- No citations, timestamps, video links or note links.
- Skip program logistics (course structure, Coursera features, certificate steps, trials, community), except career advice that matters at work.
- Interviews and stories: keep the lesson, drop the names. Keep a name only when the person or work is itself the subject (an author studied, a named theorem), and only when the profile allows it.
- Every term is explained before or where it's first used. A reader must never meet an unexplained term.

## Self-check (before you save)
Invented counts were the one recurring error in past pages. Re-read your draft against the packs, line by line:
1. **Every number.** Each figure, percentage, date, duration and price appears in the source with the same meaning. Remove any that doesn't.
2. **Every list count.** For "the five phases", "three types" and similar, count the items the source names. If the source never states a count, list the items without one. The items you list must match the source's items, in its order.
3. **Every named item.** Each framework, tool, command, function, formula, term and title is spelled as the source spells it and exists in the source.
4. **Every example.** Each one comes from the source. If none exists, leave the example out rather than make one up.
5. **Profile fit.** Every section the profile requires is present, in its order, and every core topic got full depth.

Reply with one line: topic count, whether any diagrams were included, and how many self-check fixes you made.
