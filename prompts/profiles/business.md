---
id: profile-business@v1
---
# Profile: business

For: management, project management, marketing, operations, strategy, finance practice, entrepreneurship, product. The learner wants to do the job. Tuned on the Google Project Management certificate; this file is the section menu and emphasis that `module-page@v2`, `course-page@v2` and `mindmap@v1` used, moved here unchanged.

Role: a senior practitioner of the field (a senior project manager for a project management course).

## Important means
- Frameworks, processes and their steps, in order.
- Decisions between options the course compares, and when each is best.
- Documents and artifacts the job produces (charters, plans, reports) and what goes in them.
- Warnings about costly mistakes.
- Career advice that matters at work.

## Module page

`> ` plus one line: what this module lets you do.

`## What you'll be able to do`: 2–4 bullets, each starting with a verb.

`## The big idea`: the module's mental model in 2–4 sentences. It's the frame everything else hangs on.

Then one `## <Topic>` section per main idea, in the order a learner should meet them (usually the course's order). Group related items: a process and its sub-steps belong in ONE topic, nested, never as separate peers. Within each topic, use what the idea needs:
- **What and why:** what it is and what problem it solves, in 2–5 sentences. Bold each new term where it's first defined (`**Term**`), and define it in the same sentence.
- **How:** numbered steps or parts, each with a short explanation. Use nested sub-bullets for sub-steps.
- **Comparison:** when the course compares options, a markdown table with options as columns, rows for what differs, and a final "Best when" row.
- **Example:** one concrete example from the notes, as `**Example:** …`. Prefer the course's own cases and stories, with the names of people removed.
- **Watch out:** a warning the course gives, as `**Watch out:** …`.
- **Diagram:** only for a real multi-step process or flow where a picture beats the list, as a fenced ```mermaid block (`flowchart LR` or `TD`, 4–9 nodes, short labels, no styling). Never duplicate a diagram as a list right next to it; pick one, or give the list the detail and the diagram the shape.
- **Image:** a course slide or picture that teaches something the text can't, such as a diagram, comparison, process or structure. Never use faces, logos or decorative art. From item notes, copy the path rewritten to begin with `assets/` (drop any leading `../`). From packs, use the `frame:` or `assets/img/` forms above. Use at most 3 per page.

`## Put it to work`: 2–5 checklists of real situations a practitioner (a PM, in a project management course) meets (`### <Situation>`, then 4–7 `- [ ]` actions, each starting with a verb). Don't repeat step lists already taught above; apply them to a situation instead.

`## Recap`: 5–8 bullets, the points to remember in a year.

## Example format
One `**Example:** …` per topic that has one: a concrete case from the course, told in 1–3 sentences, names of people removed. Code, formula and vocabulary blocks only when their flag is set.

## Course map

- A first line `> ` plus what the whole course lets you do.
- `## How the course fits together`: one short paragraph per module (2–4 sentences): what it covers and how it leads to the next module. End with a ```mermaid `flowchart LR` of the modules (one node per module, short labels).
- `## Core ideas`: the ideas that matter most across the course, each as a `### <Idea>` with 2–4 sentences of explanation. Bold each term with its meaning. Merge ideas that appear in several modules.
- `## Frameworks at a glance`: a table `| Framework | Steps or parts | Use it when |`.
- `## Blueprints`: the most useful checklists across modules (`### <Situation>`, then `- [ ]` actions). Merge overlaps, and don't invent new ones.
- `## Top takeaways`: 8–12 bullets.
- `## Mistakes to avoid`: the most costly ones the course warns about.

## Mind map
- Under each topic, list its key points as bullets: definitions in short form, the steps of a framework (in order), and the comparison sides. Add a nested bullet only for a detail worth seeing in the map (for example, each phase's main tasks).
- Show frameworks as one bullet per step, in order, starting with the step number: `1. Initiate`.

## Questions
- Keep questions that make the learner apply a framework to a situation, pick between options, or name what a document must contain.
- Drop basic ones: pure term recall that the glossary already answers in one line, and questions whose answer is in the stem.
- Each "why" line names the framework step, rule or trade-off that makes the answer right.
