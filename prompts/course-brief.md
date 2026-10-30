---
id: course-brief@v1
---
# Course brief (pick the profile)

Runs once per course, before any page is written. Every writer for this course then follows the profile you pick, so a wrong pick degrades every page. Decide from evidence, not from the course's subject name alone.

Input: `brief-input.md` (path in your task): the course title and description, syllabus module and lesson titles, learning objectives, item types and counts (videos, readings, labs, quizzes), the quiz count, and signals for code (code blocks, labs, notebooks, language names), math (formulas, symbols, worked problems) and downloads (templates, datasets, slides). It is your only source.

Output: `profile.json` at the output path in your task, exactly this shape:
```json
{
  "type": "business | technical | quantitative | science | language | creative | humanities | career",
  "role": "a senior <practitioner> in <field>",
  "level": "beginner | intermediate | advanced",
  "outcomes": ["Verb-first outcome", "…"],
  "emphasis": ["Topic", "…"],
  "flags": {"code": false, "formulas": false, "vocab": false, "exam": false},
  "why": "One sentence: the evidence that decided the type."
}
```

## Steps
1. **Type.** Ask what the learner mostly does with this course's material, and pick the profile built for that (each profile in `prompts/profiles/` opens with a `For:` line):
   - builds, runs or fixes systems → `technical`
   - computes, models or proves → `quantitative`
   - explains natural or medical mechanisms → `science`
   - speaks, reads or writes a new language → `language`
   - makes and judges creative work → `creative`
   - understands and argues about ideas, texts or events → `humanities`
   - acts on a job search or personal work habits → `career`
   - runs work, teams, customers or money in an organization → `business`
   When two fit, pick the one most module pages would follow, and cover the other with flags. A data-analysis course with SQL labs is `technical` with `formulas` when it teaches statistics; a finance course built on frameworks is `business` with `formulas`.
2. **Flags.** Each is true only with direct evidence in the input:
   - `code`: code blocks, programming labs, notebooks, or a programming language in titles or objectives.
   - `formulas`: formulas, equations or worked numeric problems in the syllabus or objectives.
   - `vocab`: the course teaches a language, or a large set of field terms the objectives say to learn by name.
   - `exam`: the course says it prepares for a named exam. A course certificate or a "Professional Certificate" alone is not an exam.
3. **Level.** Use the level the course states. If it states none: no prerequisites and introductory titles → `beginner`; named prerequisites → `intermediate`; titles that assume the field's basics → `advanced`.
4. **Outcomes.** 3–6, each starting with a verb, taken from the objectives and description. Rephrase for length only; never add an outcome the input does not state.
5. **Emphasis.** 3–8 topics with the strongest signals: named in objectives, tested by quizzes, given the most lessons or video minutes, or called out in the description. Use the input's own topic names.
6. **Role.** The senior practitioner a writer should sound like, in the course's field.
7. **Check.** Every field is filled, every value comes from the input, and `why` names real evidence. Write the file. Reply with one line: the type, the flags that are true, and the `why`.

## Examples

**A.** Title "Foundations of Project Management". Lessons on project life cycle, methodologies, roles, organizational culture. Objectives "Describe project management skills", "Compare Agile and Waterfall". 4 graded quizzes, no labs, no code or math. Downloads: templates.
```json
{"type": "business", "role": "a senior project manager", "level": "beginner",
 "outcomes": ["Describe what project managers do", "Explain the project life cycle", "Compare Agile and Waterfall"],
 "emphasis": ["Project life cycle", "Project management methodologies", "Organizational culture"],
 "flags": {"code": false, "formulas": false, "vocab": false, "exam": false},
 "why": "Frameworks and roles for running work in an organization; no code or math signals."}
```

**B.** Title "Data Analysis with Python". Lessons on pandas, cleaning data, descriptive statistics, regression. 6 Jupyter labs, code blocks in readings, formulas for mean, variance and the regression line. Prerequisite: basic Python.
```json
{"type": "technical", "role": "a senior data analyst", "level": "intermediate",
 "outcomes": ["Load and clean data with pandas", "Summarize data with descriptive statistics", "Fit and evaluate a linear regression"],
 "emphasis": ["Data cleaning", "pandas DataFrames", "Linear regression"],
 "flags": {"code": true, "formulas": true, "vocab": false, "exam": false},
 "why": "Six coding labs drive the course; the statistics formulas are covered by the formulas flag."}
```

**C.** Title "Spanish for Beginners: Greetings and Introductions". Lessons on greetings, numbers, ser and estar, asking questions. Dialogue videos, vocabulary readings, speaking assignments. No code or math.
```json
{"type": "language", "role": "an experienced Spanish teacher", "level": "beginner",
 "outcomes": ["Greet people and introduce yourself", "Use ser and estar correctly", "Ask and answer basic questions"],
 "emphasis": ["Greetings", "Ser and estar", "Question words"],
 "flags": {"code": false, "formulas": false, "vocab": true, "exam": false},
 "why": "Teaches a new language through dialogues, vocabulary and speaking tasks."}
```
