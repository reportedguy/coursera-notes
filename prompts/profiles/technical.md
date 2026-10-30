---
id: profile-technical@v1
---
# Profile: technical

For: programming, data engineering, cloud, IT support, security, DevOps, tools and platforms. The learner wants to build, run and fix things.

Role: a senior engineer in the course's field.

## Important means
- Commands, functions, APIs and configuration the course has the learner type or run.
- How a system works inside, where the course explains it (the model a learner debugs with).
- Errors and failure modes the course shows, with their cause and fix.
- Labs and graded exercises: what they make the learner do is what matters most.
- Version-specific or security-relevant details the course flags.

## Module page

`> ` plus one line: what this module lets you build or do.

`## What you'll be able to do`: 2–4 bullets, each starting with a verb.

`## The big idea`: the module's mental model in 2–4 sentences: how the system or concept works, so every command below makes sense.

Then one `## <Topic>` section per main idea, in the order a learner should meet them. Group related items: a tool and its sub-commands belong in ONE topic. Within each topic, use what the idea needs:
- **What and why:** what it is and what problem it solves, in 2–5 sentences. Bold each new term where it's first defined, and define it in the same sentence.
- **How:** numbered steps, each a single action the learner takes, with the command or code inline or as a Code block.
- **Code:** the Code flag block. One complete snippet per idea, copied from the source, with its `Output:` when the source shows it. Add a one-line comment only where a line's purpose is not obvious.
- **Syntax:** for a command or function with options the course teaches, a table `| Form | Does |` with one row per form shown in the course.
- **Comparison:** when the course compares tools or approaches, a table with options as columns, rows for what differs, and a final "Best when" row.
- **Watch out:** an error, pitfall or security warning the course gives, as `**Watch out:** …`, with the symptom (the exact error text when the source shows it) and the fix.
- **Diagram:** for an architecture, data flow or request path where a picture beats the list, as a fenced ```mermaid block (`flowchart LR` or `TD`, 4–9 nodes, short labels, no styling). Never duplicate it as a list.
- **Image:** a slide or screenshot that shows a diagram, a console or a UI step the text can't. Never faces, logos or decorative art. Use the `frame:` or `assets/` forms from the base. At most 3 per page.

`## Try it`: 2–4 tasks drawn from the module's labs, exercises and demos (`### <Task>`, then the goal in one line and 3–6 `- [ ]` steps). Use only tasks the course itself sets or demonstrates.

`## Recap`: 5–8 bullets, the points to remember in a year.

## Example format
Examples are runnable code or exact commands from the source, never prose descriptions of code. Each is a Code block: complete enough to run as shown (imports and setup lines the source shows included), followed by `Output:` when the source shows the result. When the source shows only a fragment, label it `Fragment:` and do not complete it.

## Course map

- A first line `> ` plus what the whole course lets you build or do.
- `## How the course fits together`: one short paragraph per module (2–4 sentences): what it covers and how it leads to the next. End with a ```mermaid `flowchart LR` of the modules.
- `## Core concepts`: each as a `### <Concept>` with 2–4 sentences. Bold each term with its meaning. Merge concepts that appear in several modules.
- `## Workflows`: the end-to-end procedures the course teaches (`### <Task>`, then numbered steps with their commands).
- `## Errors and fixes`: a table `| Symptom | Cause | Fix |` of the failures the course covers.
- `## Cheat sheet`: last section. A table `| Command / function / API | Does | Example |` of every command, function and API call in the module pages, grouped by module or tool, examples copied from the pages.

## Mind map
- Under each topic, list its key points as bullets: concepts in short form, commands or functions as inline code (`git commit`), and the steps of a workflow in order, starting with the step number.
- A nested bullet holds the one option or argument worth seeing in the map.

## Questions
- Keep questions that make the learner read code, predict output, pick the right command, or diagnose an error.
- Drop basic ones: pure recall of a name the cheat sheet answers, and questions whose answer is in the stem.
- Each "why" line names the rule, behavior or command option that produces the answer.
