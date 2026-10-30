---
name: curate-questions
description: Pick which of a course's real quiz questions are worth practising, and write a one-line "why" for each kept answer. Feeds the Study Notebook's Question practice page.
---

Inputs, all in `<data_root>/pages/<course>/`:
- `qa-candidates.json`: the questions you have answered on Coursera, with options, the correct answer and Coursera's feedback.
- `profile.json`
- the module pages `mNN.md`

Write exactly two files in the same folder:

1. **`qa-drop.json`**: `[{"id": "...", "reason": "..."}]`, the questions not worth practising.
   - Drop basic recall with obvious distractors, trivia (statistics, dates or names that aren't core), and questions whose answer is given away by the wording.
   - Keep questions that test applying, judging or telling close concepts apart, and anything in the profile's `emphasis`.
   - For `exam` courses, keep more: anything that resembles exam-style items.
   - The reason is at most 12 words.
2. **`qa-why.json`**: `{"<id>": "<why>"}` for every kept question.
   - Each why is at most 25 words. It says why the right answer is right, and where it helps, why the tempting wrong one is wrong.
   - Use only Coursera's feedback and the module pages. Never contradict the given correct answer.

Reply in one line: kept versus dropped counts.
